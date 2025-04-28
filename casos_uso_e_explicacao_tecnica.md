# Casos de Uso e Explicação Técnica

## Casos de Uso

### 1. Preenchimento de Códigos de Importador (CNPJ)

**Cenário**: Um registro de importação tem o campo `consignee_code` (CNPJ do importador) ausente.

**Solução**:
1. O sistema identifica que o CNPJ está ausente
2. Busca registros com o mesmo código NCM, país de origem e transportadora
3. O LLM identifica padrões de correspondência entre Volvo Logistics e CNPJs específicos
4. Infere o CNPJ mais provável com base nos registros similares
5. Fornece uma explicação sobre o raciocínio usado na inferência

**Exemplo**:
```
Registro: "2025-02-01","87089200","GB","MARITIMA","PORTO DE PARANAGUA",,"VOLVO LOGISTICS","DUIMP - Crawler Complete"

Inferência: "43.999.424/0001-14"

Explicação: Este CNPJ foi inferido porque 85% dos registros com a transportadora 'VOLVO LOGISTICS', códigos NCM na série 87XXXXX e origem GB estão associados a este mesmo código de importador.
```

### 2. Preenchimento de Modo de Transporte

**Cenário**: Um registro tem o campo `transport_mode_pt` ausente.

**Solução**:
1. O sistema busca registros com o mesmo código NCM e local de desembaraço
2. O LLM analisa a consistência do modo de transporte para esse local
3. Infere o modo de transporte com base na combinação de local e tipo de produto

**Exemplo**:
```
Registro: "2025-02-01","90328990","MX",,,"04.581.264/0004-80","SENSATA TECHNOLOGIES","DUIMP - Crawler Partial"

Inferência: "AEREA"

Explicação: Produtos eletrônicos da série 9032XXXX provenientes do México são tipicamente transportados via aérea, conforme observado em 92% dos casos similares. Adicionalmente, a empresa SENSATA TECHNOLOGIES importa predominantemente por via aérea.
```

### 3. Preenchimento de Informações de Transportadora

**Cenário**: Um registro tem o campo `shipper_name` ausente.

**Solução**:
1. O sistema analisa registros com o mesmo código NCM, país e importador
2. O LLM analisa as transportadoras mais frequentes para essa combinação
3. Infere a transportadora com maior probabilidade

**Exemplo**:
```
Registro: "2025-02-01","73181500","DE","MARITIMA","PORTO DE PARANAGUA","43.999.424/0001-14",,"DUIMP - Crawler Complete"

Inferência: "VOLVO LOGISTICS"

Explicação: Para produtos do código NCM 7318XXXX, importados pela entidade com CNPJ 43.999.424/0001-14, a transportadora VOLVO LOGISTICS é utilizada em 78% dos casos, especialmente para cargas provenientes da Alemanha (DE).
```

## Explicação Técnica Detalhada

### 1. Pré-processamento e Análise de Dados

O módulo `utils.py` implementa várias funções essenciais para o processamento de dados:

#### 1.1 Identificação de Dados Ausentes
```python
def find_missing_data(df: pd.DataFrame) -> Dict[int, List[str]]:
    missing_data = {}
    for idx, row in df.iterrows():
        missing_cols = row.index[row.isna()].tolist()
        if missing_cols:
            missing_data[idx] = missing_cols
    return missing_data
```

Esta função itera sobre cada linha do DataFrame, identifica células vazias (NaN) e registra quais colunas estão ausentes em cada linha. Retorna um dicionário onde as chaves são os índices das linhas e os valores são listas das colunas ausentes.

#### 1.2 Algoritmo de Busca de Registros Similares

O algoritmo de busca de registros similares é uma parte crítica do sistema e segue uma abordagem de filtragem progressiva:

1. **Filtragem Inicial**: Prioriza correspondências em colunas críticas como código NCM e país de origem
2. **Filtragem Secundária**: Aplica filtros adicionais como modo de transporte ou local de desembaraço
3. **Pontuação de Relevância**: Atribui pontuações para cada registro filtrado com base em correspondências exatas
4. **Ordenação e Seleção**: Retorna os registros mais relevantes para o processo de inferência

```python
def find_similar_rows(target_row: pd.Series, reference_df: pd.DataFrame, match_columns: List[str]) -> pd.DataFrame:
    # Filtragem por NCM e país
    filtered_df = reference_df.copy()
    if 'ncm_code' in target_row.index and not pd.isna(target_row['ncm_code']):
        filtered_df = filtered_df[filtered_df['ncm_code'] == target_row['ncm_code']]
    
    # Cálculo de pontuação para cada linha
    scored_rows = []
    for idx, row in filtered_df.iterrows():
        score = 0
        for col in match_columns:
            if col in target_row.index and col in row.index and not pd.isna(target_row[col]) and not pd.isna(row[col]):
                if target_row[col] == row[col]:
                    if col in ['ncm_code', 'country_origin_acronym']:
                        score += 3  # Peso maior para colunas importantes
                    else:
                        score += 1
        scored_rows.append((idx, score, row))
    
    # Ordenação e seleção
    scored_rows.sort(key=lambda x: x[1], reverse=True)
    # ...
```

### 2. Engenharia de Prompt

O sistema utiliza uma engenharia de prompt sofisticada para maximizar a eficácia das inferências do LLM:

#### 2.1 Estrutura do Prompt

```
Você é um especialista em análise de dados de importação/exportação. Sua tarefa é inferir valores ausentes em registros de importação.

Registro com dados ausentes:
{row_data}

As colunas ausentes que precisam ser preenchidas são:
{missing_columns}

Aqui estão registros semelhantes de nossos dados históricos que podem ajudar:
{similar_rows}

Descrição das colunas:
{column_descriptions}

[...instruções específicas...]

Forneça sua resposta como um objeto JSON válido contendo os nomes das colunas ausentes e seus valores inferidos, além das explicações.
```

#### 2.2 Componentes Essenciais do Prompt

1. **Contextualização do Problema**: Define claramente o papel do LLM e o objetivo da tarefa
2. **Dados do Registro Alvo**: Fornece ao LLM o registro com valores ausentes
3. **Colunas Ausentes**: Especifica exatamente quais colunas precisam ser preenchidas
4. **Registros Semelhantes**: Fornece exemplos relevantes do conjunto de dados de referência
5. **Descrições das Colunas**: Explica o significado e formato de cada coluna
6. **Instruções Específicas**: Guia o LLM sobre como considerar diferentes tipos de dados
7. **Formato de Resposta**: Solicita uma resposta estruturada em formato JSON

### 3. Processamento com LLM

A classe `DataCompletionAgent` no arquivo `agent.py` gerencia a interação com o LLM:

```python
def __init__(self, model_name="gpt-3.5-turbo"):
    api_key = os.getenv("OPENAI_API_KEY")
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
```

O agente utiliza temperatura 0 para maximizar a consistência e previsibilidade das inferências.

#### 3.1 Processamento de Lotes

O processamento em lotes permite balancear eficiência e utilização da API:

```python
# Trecho simplificado do método process_dataframe
for idx, missing_cols in tqdm(missing_data_map.items(), desc="Processing rows"):
    row = target_df.iloc[idx]
    
    # Encontra linhas similares
    similar = find_similar_rows(row, reference_df, match_columns)
    
    # Prepara dados para o LLM
    inference_data = prepare_inference_data(row, missing_cols, similar)
    
    # Chama o LLM para inferir valores ausentes
    response = self.chain.invoke(inference_data)
    
    # Processa a resposta...
```

#### 3.2 Tratamento de Resposta

O sistema implementa múltiplas estratégias para extrair informações da resposta do LLM:

```python
# Extrair o JSON da resposta (pode estar em vários formatos)
try:
    # Tentar avaliar como expressão Python
    response_data = eval(response_text)
except:
    # Tentar analisar como JSON
    try:
        response_data = json.loads(response_text)
    except:
        # Último recurso: extrair apenas a parte JSON
        import re
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            response_data = json.loads(match.group(0))
```

Esta abordagem robusta garante que o sistema possa extrair valores inferidos mesmo quando o formato da resposta varia.

### 4. Análise e Explicabilidade

Um diferencial importante deste sistema é a geração de explicações para cada inferência:

```python
# Processar a resposta
for key, value in response_data.items():
    if key.startswith("explicacao_"):
        # Extrair o nome da coluna da explicação
        col_name = key[11:]
        explanations[col_name] = value
    elif key in missing_cols:
        # Se for uma coluna ausente
        inferred_values[key] = value

# Compilar explicações
explanation_text = []
for col in missing_cols:
    if col in explanations:
        explanation_text.append(f"{col}: {explanations[col]}")
```

As explicações são essenciais para:
1. Permitir validação manual das inferências
2. Construir confiança no sistema automatizado
3. Identificar padrões recorrentes nos dados
4. Melhorar o sistema iterativamente com base nos resultados

## Considerações Técnicas Adicionais

### Otimização de Desempenho

1. **Filtragem Eficiente**: O uso de filtragem progressiva reduz o escopo de busca
2. **Limitação de Registros Similares**: Apenas os registros mais relevantes são incluídos no prompt
3. **Processamento em Lotes**: Balancea a utilização da API com a velocidade de processamento

### Robustez do Sistema

1. **Tratamento de Exceções**: Implementação de tratamento de erros em cada etapa
2. **Múltiplas Estratégias de Parsing**: Flexibilidade para lidar com diferentes formatos de resposta
3. **Logging Detalhado**: Registra alertas e erros para facilitar a depuração

### Extensibilidade

O sistema é projetado para ser facilmente extensível:

1. **Configuração de Diferentes Modelos**: Suporte para diferentes modelos LLM através de parâmetros
2. **Personalização de Prompt**: O template de prompt pode ser ajustado para diferentes tipos de dados
3. **Parametrização de Busca**: Os critérios de similaridade podem ser ajustados por configuração 