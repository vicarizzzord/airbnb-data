
# Dados airbnb da cidade do Rio de Janeiro (2024/2025)

## Descrição

Um projeto de engenharia de dados no qual é utilizada a arquitetura de medalhão para tratamento e inserção dos dados em um banco de dados [Postgre](https://www.postgresql.org/) local, utilizando [Docker](https://www.docker.com/). O projeto também faz requisições na API do [ExchangeRate](https://www.exchangerate-api.com/), pois a base de dados está com valores descritos em dólar USD, e também faz o download dos dados utilizados no projeto de forma automatizada.



## Stack utilizada

- **Tratamento e processamento dos dados:** Python e Pandas
- **Banco de dados:** PostgreSQL e Docker



## Fluxo do sistema
### Bronze
Os dados são baixados e carregados de forma crua em dataframes e salvos no banco de dados com a tag `_bronze`

### Prata
Depois de carregados em dataframes, há o tratamento das informações faltantes e formatação dos tipos de dados e salvos no banco de dados com a tag `_silver`

### Ouro
Com os dados tratados e no formato correto, é realizado um pipeline para a criação de uma nova tabela com informações agrupadas, para a realização de análises e criação de infográficos para análises. É salvo com a tag `_gold`
## Requisitos


- Docker
- Python
- API key do ExchangeRate
## Instrução de uso

1. Inicialize o banco de dados com o Docker, rodando:
```bash 
    docker start postgres_container
```
Obs: por estar rodando localmente, as configurações do container são básicas, sem nenhum tipo de configuração adicional

2. Adicione a sua API Key no arquivo das variáveis de ambiente `.env`

3. Execute o comando, dentro do diretório root do projeto, para ser realizada a  instalação dos módulos necessários para o projeto funcionar corretamente
```bash
    pip install -r requirements.txt
```

Com o banco de dados rodando com o docker e a API key do ExchangeRate inserida no arquivo das variáveis de ambiente, ja é possível rodar o sistema perfeitamente.

