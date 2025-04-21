import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import pandas as pd
from tqdm import tqdm
import json

from utils import find_missing_data, find_similar_rows, prepare_inference_data

load_dotenv()

# Template for inferring missing values
INFERENCE_TEMPLATE = """
Você é um especialista em análise de dados de importação/exportação. Sua tarefa é inferir valores ausentes em registros de importação.

Registro com dados ausentes:
{row_data}

As colunas ausentes que precisam ser preenchidas são:
{missing_columns}

Aqui estão registros semelhantes de nossos dados históricos que podem ajudar:
{similar_rows}

Descrição das colunas:
{column_descriptions}

Analise cuidadosamente o registro atual e os registros semelhantes. Observe os padrões comuns, relacionamentos e lógica de negócios entre os campos. 

Importante:
- Para nomes de empresas (shipper_name), considere variações de escrita, abreviações ou diferenças ortográficas.
- Para códigos de empresa (consignee_code), busque padrões consistentes para o mesmo tipo de produto ou origem.
- Para modos de transporte (transport_mode_pt) e locais de desembaraço (clearance_place_entry), observe a relação lógica com outros campos.

Com base nos padrões encontrados, infira o valor mais provável para cada coluna ausente.

Para cada coluna ausente, informe também uma explicação breve do motivo pelo qual você considera esse valor o mais adequado.

Forneça sua resposta como um objeto JSON válido contendo os nomes das colunas ausentes e seus valores inferidos, além das explicações.

Por exemplo, se precisa preencher as colunas "transport_mode_pt" e "consignee_code", sua resposta deve ter este formato:

{{
  "transport_mode_pt": "VALOR_INFERIDO",
  "consignee_code": "VALOR_INFERIDO",
  "explicacao_transport_mode_pt": "Explicação para o valor inferido",
  "explicacao_consignee_code": "Explicação para o valor inferido"
}}
"""

class DataCompletionAgent:
    def __init__(self, model_name="gpt-3.5-turbo"):
        # Carregar a chave API diretamente
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        print(f"Using API key: {api_key[:10]}...{api_key[-5:]}")
        
        # Inicializar o LLM com a chave API explícita
        self.llm = ChatOpenAI(
            temperature=0, 
            model_name=model_name,
            openai_api_key=api_key
        )
        
        self.prompt = PromptTemplate(
            input_variables=["row_data", "missing_columns", "similar_rows", "column_descriptions"],
            template=INFERENCE_TEMPLATE
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        
    def process_dataframe(self, 
                         target_df: pd.DataFrame, 
                         reference_df: pd.DataFrame, 
                         match_columns: List[str],
                         batch_size: int = 10,
                         max_similar_rows: int = 5) -> pd.DataFrame:
        """
        Process the target dataframe to fill in missing values using reference data and LLM inference.
        
        Args:
            target_df: DataFrame with missing values
            reference_df: Reference DataFrame for finding similar rows
            match_columns: Columns to use for matching similar rows
            batch_size: Number of rows to process in each batch
            max_similar_rows: Maximum number of similar rows to include in the prompt
            
        Returns:
            DataFrame with filled missing values
        """
        # Make a copy to avoid modifying the original
        result_df = target_df.copy()
        
        # Add a column for explanations
        result_df['explicacoes_inferencia'] = ""
        
        # Find rows with missing data
        missing_data_map = find_missing_data(target_df)
        
        print(f"Found {len(missing_data_map)} rows with missing data")
        
        # Process rows with missing data
        for idx, missing_cols in tqdm(missing_data_map.items(), desc="Processing rows"):
            row = target_df.iloc[idx]
            
            # Find similar rows
            similar = find_similar_rows(row, reference_df, match_columns)
            
            if len(similar) == 0:
                print(f"Warning: No similar rows found for row {idx}")
                continue
                
            # Limit number of similar rows to reduce token usage
            similar = similar.head(max_similar_rows)
            
            # Prepare data for LLM
            inference_data = prepare_inference_data(row, missing_cols, similar)
            
            try:
                # Call LLM to infer missing values
                response = self.chain.invoke(inference_data)
                
                # Corrigindo a forma de acessar a resposta do LLM
                # A resposta agora é um dicionário com vários campos
                if hasattr(response, 'text'):
                    # Formato antigo (para compatibilidade)
                    response_text = response.text
                elif isinstance(response, dict) and 'text' in response:
                    # Algumas versões retornam um dicionário com a chave 'text'
                    response_text = response['text']
                elif isinstance(response, dict) and 'content' in response:
                    # Outras versões retornam um dicionário com a chave 'content'
                    response_text = response['content']
                else:
                    # Se for uma string direta ou outro formato
                    response_text = str(response)
                
                # Extrair o JSON da resposta (pode estar em vários formatos)
                try:
                    # Tentar avaliar como expressão Python
                    response_data = eval(response_text)
                except:
                    # Tentar analisar como JSON
                    try:
                        response_data = json.loads(response_text)
                    except:
                        # Último recurso: extrair apenas a parte JSON da resposta
                        import re
                        json_pattern = r'\{.*\}'
                        match = re.search(json_pattern, response_text, re.DOTALL)
                        if match:
                            response_data = json.loads(match.group(0))
                        else:
                            raise ValueError(f"Couldn't extract JSON from response: {response_text}")
                
                # Inicializar dicionários para valores e explicações
                inferred_values = {}
                explanations = {}
                
                # Processar a resposta
                for key, value in response_data.items():
                    if key.startswith("explicacao_"):
                        # Extrair o nome da coluna da explicação (remover o prefixo "explicacao_")
                        col_name = key[11:]
                        explanations[col_name] = value
                    elif key != "explicacoes" and key != "valores" and key in missing_cols:
                        # Se não for uma chave de metadados e for uma coluna ausente
                        inferred_values[key] = value
                
                # Se temos o formato antigo com valores e explicações separados
                if "valores" in response_data and isinstance(response_data["valores"], dict):
                    for col, value in response_data["valores"].items():
                        inferred_values[col] = value
                
                if "explicacoes" in response_data and isinstance(response_data["explicacoes"], dict):
                    for col, expl in response_data["explicacoes"].items():
                        explanations[col] = expl
                
                # Update the result dataframe with inferred values
                for col, value in inferred_values.items():
                    result_df.at[idx, col] = value
                
                # Compilar todas as explicações em uma única string
                explanation_text = []
                for col in missing_cols:
                    if col in explanations:
                        explanation_text.append(f"{col}: {explanations[col]}")
                    elif col in inferred_values:
                        explanation_text.append(f"{col}: Valor inferido sem explicação detalhada")
                
                # Adicionar explicação à coluna de explicações
                result_df.at[idx, 'explicacoes_inferencia'] = " | ".join(explanation_text)
                    
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                
        return result_df 