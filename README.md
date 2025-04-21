# Agente de Completamento de Dados de Importação

Este projeto utiliza LangChain e LLMs para inferir valores ausentes em dados CSV de importação/exportação, encontrando registros semelhantes e utilizando reconhecimento de padrões.

## Visão Geral

O sistema lê um arquivo CSV com dados ausentes (`duimp_202502.csv`), identifica quais colunas estão faltando em cada linha e utiliza um Modelo de Linguagem Grande (LLM) para inferir os valores ausentes com base em registros semelhantes encontrados em um conjunto de dados de referência (`duimp_completa__202412.csv`).

O projeto inclui:
- Um agente LangChain para processar dados CSV com valores ausentes
- Ferramentas para encontrar registros semelhantes em um conjunto de dados de referência
- Engenharia de prompts para inferência eficaz com LLM
- Análise de padrões de dados ausentes
- Geração de explicações para cada inferência realizada

## Estrutura do Projeto

```
├── main.py                         # Script principal para executar o agente
├── run_with_explanations.py        # Script para executar com explicações
├── agent.py                        # Implementação do agente LangChain
├── utils.py                        # Funções utilitárias para processamento CSV
├── analyze.py                      # Script para analisar padrões de dados ausentes
├── prompt_engineering.py           # Ferramentas para criar prompts eficazes
├── requirements.txt                # Dependências do projeto
└── .env                            # Variáveis de ambiente (chaves de API)
```

## Requisitos

- Python 3.8+
- Chave de API OpenAI

## Instalação

1. Clone este repositório
2. Instale os pacotes necessários:

```bash
pip install -r requirements.txt
```

3. Crie um arquivo `.env` com sua chave de API OpenAI:

```
OPENAI_API_KEY=sua_chave_api_openai_aqui
```

## Uso

### Executando o Agente Principal

Execute o script principal com parâmetros padrão:

```bash
python main.py
```

Ou personalize com argumentos de linha de comando:

```bash
python main.py --target duimp_202502.csv --reference duimp_completa__202412.csv --output duimp_completed.csv --model gpt-3.5-turbo
```

### Executando com Explicações

Para gerar explicações detalhadas para cada inferência:

```bash
python run_with_explanations.py
```

### Analisando Padrões de Dados Ausentes

Para analisar os padrões de dados ausentes em seu arquivo CSV:

```bash
python analyze.py
```

### Gerando Exemplos de Prompts

Para gerar exemplos de prompts para treinamento de LLM:

```bash
python prompt_engineering.py
```

## Como Funciona

1. **Carregamento de Dados**: O agente lê o arquivo CSV alvo com dados ausentes.
2. **Identificação de Dados Ausentes**: Para cada linha, identifica quais colunas têm valores ausentes.
3. **Busca de Registros Semelhantes**: Procura no conjunto de dados de referência registros com características semelhantes.
4. **Construção de Prompt**: Constrói um prompt para o LLM contendo:
   - A linha com dados ausentes
   - As colunas que precisam ser preenchidas
   - Linhas semelhantes do conjunto de dados de referência
   - Descrições das colunas
5. **Inferência do LLM**: O LLM usa reconhecimento de padrões para inferir os valores mais prováveis para as colunas ausentes.
6. **Compilação de Resultados**: Os valores inferidos são adicionados ao conjunto de dados de saída.
7. **Geração de Explicações**: O LLM fornece explicações detalhadas sobre o raciocínio por trás de cada inferência.

## Argumentos de Linha de Comando

- `--target`: Caminho para o arquivo CSV com dados ausentes (padrão: `duimp_202502.csv`)
- `--reference`: Caminho para o arquivo CSV de referência com dados completos (padrão: `duimp_completa__202412.csv`)
- `--output`: Caminho para salvar o arquivo CSV completado (padrão: `duimp_completed.csv` ou `duimp_completed_with_explanations.csv`)
- `--model`: Modelo LLM a ser usado (padrão: `gpt-3.5-turbo`)
- `--batch-size`: Número de linhas a serem processadas em cada lote (padrão: 10)
- `--max-similar`: Número máximo de linhas semelhantes a incluir em cada prompt (padrão: 5) 