<h1 align='center'>Desafio de Processamento de Dados - Principia 🎓</h1>

<p align="center">
  <img src="https://c5gwmsmjx1.execute-api.us-east-1.amazonaws.com/prod/dados_processo_seletivo/logo_empresa/147549/principia.jpg" alt="Logo Principia">
</p>

O objetivo do desafio foi validar e processar dados de clientes a partir de um arquivo Excel, utilizando diversas regras de validação, e gerar arquivos de saída com os resultados.

<br>

## 📋 Descrição do Desafio

O desafio consistiu nas seguintes etapas:

**1. Validação dos dados de clientes**

- O CPF do cliente é válido?
- O cliente possui nome completo?
- A data de nascimento é válida?
- É uma idade possível? (Maiores de 17 anos)
- O e-mail é válido?
- O telefone informado está no formato certo?
- Validar o CEP utilizando a API: [ViaCEP](https://viacep.com.br/)
- Validar o endereço informado utilizando a API: [ViaCEP](https://viacep.com.br/)

<br>

**2. Exportação de dados inválidos para um arquivo Excel**

- `clientes_invalidos.xlsx` com o motivo da invalidação.

<br>

**3. Comparação de clientes válidos com um arquivo de sistema `sistema.xlsx`**

- Se o cliente já tiver cadastro, ele receberá o tipo `A` de atualização.
- Se o cliente não tiver cadastro, ele receberá o tipo `I` de inserção.

<br>

**4. Exportação de clientes válidos para um arquivo JSON**

- `clientes_para_subir.json`.

<br>

## 🛠 Implementação

A solução foi implementada em um script Python `processamento.py` que realiza as seguintes etapas:

<br>

### 📚 Importação de Bibliotecas

Importei as bibliotecas necessárias para manipulação de dados, validação e interação com APIs.

<details>
<summary>Libs</summary>

```python
import pandas as pd
import re
import requests
from datetime import datetime
import json
import logging
```
</details>

<br>

### 🔧 Padronização e Limpeza de Dados

Esta função converte textos para maiúsculas, remove espaços em branco, formata CPF e data de nascimento, remove caracteres não numéricos de telefones, padroniza o nome da faculdade e elimina duplicatas.

<details>
  <summary>Código da função</summary>

```python
# Função para padronizar e limpar os dados
def padronizar_e_limpar_dados(df):
    """
    Padroniza e limpa os dados do DataFrame.
    """
    df['NOME'] = df['NOME'].str.upper().str.strip()
    df['Endereço'] = df['Endereço'].str.upper().str.strip()
    df['Bairro'] = df['Bairro'].str.upper().str.strip()
    df['Cidade'] = df['Cidade'].str.upper().str.strip()
    df['Estado'] = df['Estado'].str.upper().str.strip()
    df['Curso'] = df['Curso'].str.upper().str.strip()
    df['CPF'] = df['CPF'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(11)).str.strip()
    df['Data de Nascimento'] = pd.to_datetime(df['Data de Nascimento'], errors='coerce').dt.strftime('%Y-%m-%d').str.strip()
    df['Telefone'] = df['Telefone'].apply(lambda x: re.sub(r'\D', '', str(x)).strip())
    df['Faculdade'] = df['Faculdade'].str.lower().str.strip()
    df['CEP'] = df['CEP'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(8)).str.strip()
    df = df.drop_duplicates()
    return df
```
</details>

<br>

### 🔍 Funções de Validação

A seguir, estão as funções de validação implementadas para cada um dos campos específicos.

<br>

<details>
<summary>Validação do CPF</summary>

```python
# Função para validar CPF
def validar_cpf(cpf):
    """
    Valida se o CPF é válido usando dígitos verificadores.
    """
    cpf = re.sub(r'\D', '', str(cpf)).zfill(11)
    if len(cpf) != 11:
        return False
    if cpf in [cpf[0] * 11 for _ in range(10)]:
        return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i+1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True
```
</details>

<details>
<summary>Validação de e-mail</summary>

```python
# Função para validar email
def validar_email(email):
    """
    Verifica se o e-mail está no formato correto usando expressões regulares
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
```
</details>

<details>
<summary>Validação de telefone</summary>

```python
# Função para validar telefone
def validar_telefone(telefone):
    """
    Verifica se o telefone está no formato correto (10 ou 11 dígitos)
    """
    return re.match(r'^\d{10,11}$', str(telefone)) is not None
```
</details>

<details>
<summary>Validação de data de nascimento e idade</summary>

```python
# Função para validar a data de nascimento e idade
def validar_data_nascimento(data_nascimento):
    """
    Verifica se a data é válida e se a pessoa tem mais de 17 anos
    """
    try:
        data = datetime.strptime(data_nascimento, '%Y-%m-%d')
        idade = (datetime.now() - data).days // 365
        return idade >= 18
    except ValueError:
        return False
```
</details>

<details>
<summary>Validação de nome completo</summary>

```python
# Função para validar nome completo
def validar_nome_completo(nome):
    """
    Verifica se o nome é composto por pelo menos duas palavras
    """
    return len(nome.split()) >= 2
```
</details>

<details>
<summary>Validação de CEP com a API ViaCEP</summary>

```python
# Função para validar CEP utilizando a API ViaCEP
def validar_cep(cep):
    """
    Valida o CEP utilizando a API ViaCEP
    """
    cep = re.sub(r'\D', '', str(cep))
    try:
        response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
        if response.status_code == 200:
            data = response.json()
            if data.get('erro'):
                return False, {}
            return True, data
        return False, {}
    except requests.RequestException as e:
        logging.error(f"Erro ao validar CEP: {e}")
        return False, {}
```
</details>

<details>
<summary>Validação de endereço com a API ViaCEP</summary>

```python
# Função para validar endereço utilizando os dados da API ViaCEP
def validar_endereco(data, endereco, bairro, cidade, estado):
    """
    Valida o endereço com base nos dados retornados pela API ViaCEP
    """
    return (data.get('logradouro', '').upper() in endereco and
            data.get('bairro', '').upper() == bairro and
            data.get('localidade', '').upper() == cidade and
            data.get('uf', '').upper() == estado)
```
</details>

<br>

### 🧩 Função Principal de Processamento

A função principal carrega os dados, padroniza-os, valida cada registro e exporta os resultados.

<details>
  <summary>Código da função</summary>

```python
# Função principal de processamento
def processar_dados():
    logging.info("Iniciando processamento dos dados...")

    # Carregar e padronizar os dados
    caminho_arquivo = 'dados.xlsx'
    try:
        df = pd.read_excel(caminho_arquivo)
    except FileNotFoundError as e:
        logging.error(f"Erro ao carregar o arquivo: {e}")
        return
    
    df_limpo = padronizar_e_limpar_dados(df)
    logging.info("Dados padronizados.")

    # Validar os dados
    clientes_validos = []
    clientes_invalidos = []
    clientes_desconsiderados = []

    for index, row in df_limpo.iterrows():
        motivos_invalidos = []

        if not validar_cpf(row['CPF']):
            motivos_invalidos.append("CPF inválido")
        if not validar_nome_completo(row['NOME']):
            motivos_invalidos.append("Nome incompleto")
        if not validar_data_nascimento(row['Data de Nascimento']):
            motivos_invalidos.append("Data de nascimento inválida ou idade menor que 18")
        if not validar_email(row['Email']):
            motivos_invalidos.append("Email inválido")
        if not validar_telefone(row['Telefone']):
            motivos_invalidos.append("Telefone inválido")
        cep_valido, data_cep = validar_cep(row['CEP'])
        if not cep_valido:
            motivos_invalidos.append("CEP inválido")
        elif not validar_endereco(data_cep, row['Endereço'], row['Bairro'], row['Cidade'], row['Estado']):
            motivos_invalidos.append("Endereço não corresponde ao CEP")

        if motivos_invalidos:
            row['Motivo'] = ", ".join(motivos_invalidos)
            clientes_invalidos.append(row)
        else:
            clientes_validos.append(row)

    df_clientes_validos = pd.DataFrame(clientes_validos)
    df_clientes_invalidos = pd.DataFrame(clientes_invalidos)

    df_clientes_invalidos.to_excel('clientes_invalidos.xlsx', index=False)
    logging.info("Validação concluída. Arquivo 'clientes_invalidos.xlsx' foi gerado.")

    # Comparar com o sistema
    sistema_path = 'sistema.xlsx'
    try:
        df_sistema = pd.read_excel(sistema_path)
    except FileNotFoundError as e:
        logging.error(f"Erro ao carregar o arquivo do sistema: {e}")
        return

    if not df_clientes_validos.empty:
        df_clientes_validos['CPF'] = df_clientes_validos['CPF'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(11))
        df_sistema['cpf'] = df_sistema['cpf'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(11))
        df_clientes_validos['TIPO'] = 'I'
        df_clientes_validos.loc[df_clientes_validos['CPF'].isin(df_sistema['cpf']), 'TIPO'] = 'A'
        logging.info("Comparação concluída.")

        # Converter para JSON
        def converter_para_json(df):
            clientes = []
            for index, row in df.iterrows():
                cliente = {
                    "id": f"{row['Faculdade']}-{row['CPF']}",
                    "agrupador": row['Faculdade'],
                    "tipoPessoa": "FISICA",
                    "nome": row['NOME'],
                                        "cpf": row['CPF'],
                    "dataNascimento": row['Data de Nascimento'],
                    "tipo": row['TIPO'],
                    "enderecos": [
                        {
                            "cep": row['CEP'],
                            "logradouro": row['Endereço'],
                            "bairro": row['Bairro'],
                            "cidade": row['Cidade'],
                            "numero": str(row['Numero']),
                            "uf": row['Estado']
                        }
                    ],
                    "emails": [
                        {
                            "email": row['Email']
                        }
                    ],
                    "telefones": [
                        {
                            "tipo": "CELULAR",
                            "ddd": row['Telefone'][:2],
                            "telefone": row['Telefone'][2:]
                        }
                    ],
                    "informacoesAdicionais": [
                        {
                            "campo": "cpf_aluno",
                            "linha": index + 2,
                            "coluna": 2,
                            "valor": row['CPF']
                        },
                        {
                            "campo": "registro_aluno",
                            "linha": index + 2,
                            "coluna": 12,
                            "valor": str(row['RA'])
                        },
                        {
                            "campo": "nome_aluno",
                            "linha": index + 2,
                            "coluna": 1,
                            "valor": row['NOME']
                        }
                    ]
                }
                clientes.append(cliente)
            return clientes

        clientes_json = converter_para_json(df_clientes_validos)

        output_json_path = 'clientes_para_subir.json'
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(clientes_json, f, ensure_ascii=False, indent=4)

        logging.info("Conversão concluída. Arquivo 'clientes_para_subir.json' foi gerado.")
    else:
        logging.info("Nenhum cliente válido encontrado para comparação e exportação.")
        
    # Exibir resultados finais
    total_clientes = len(df)
    total_validos = len(df_clientes_validos)
    total_invalidos = len(df_clientes_invalidos)
    total_desconsiderados = total_clientes - total_validos - total_invalidos

    print(f"Número total de clientes analisados: {total_clientes}")
    print(f"Número total de clientes válidos: {total_validos}")
    print(f"Número total de clientes inválidos: {total_invalidos}")
    print(f"Número total de clientes desconsiderados: {total_desconsiderados}")

if __name__ == "__main__":
    processar_dados()
```
</details>

<br>

## 🧑‍💻 Como Pensei para Resolver, e Por que Fiz Assim?

Para resolver o desafio, minha principal preocupação foi garantir que o código fosse fácil de manter, eficiente e preciso. Optei por dividir o processo em etapas claras para que cada parte do código tivesse uma responsabilidade específica. Isso não apenas facilita a depuração e testes, mas também permite que futuras mudanças sejam implementadas de forma isolada, sem afetar outras partes do sistema.

Escolhi usar pandas pela sua robustez e facilidade de uso na manipulação de dados em Excel, essencial para ler e limpar os dados de entrada. A biblioteca re foi escolhida pela sua eficiência em trabalhar com expressões regulares, que são fundamentais para validações de formato como CPF e e-mail. Usei requests para acessar a API ViaCEP porque é uma biblioteca simples e direta para fazer requisições HTTP, garantindo que os endereços fossem validados com precisão.

A ideia de padronizar os dados antes de validar surgiu da necessidade de evitar problemas comuns como diferenças de capitalização ou espaços em branco desnecessários, que poderiam levar a falhas de validação. As funções específicas para cada tipo de validação ajudam a manter o código organizado e fácil de entender, facilitando a identificação de possíveis pontos de falha e ajustes necessários.

Separar os dados válidos dos inválidos e exportá-los para arquivos distintos permite um controle mais claro sobre o estado de cada registro, ajudando a identificar rapidamente os problemas e agir sobre eles. Além disso, essa abordagem modular assegura que cada parte do processo possa ser reutilizada ou adaptada para diferentes contextos ou projetos futuros, aumentando a flexibilidade do código.

<br>

## 🏃‍♂️ Como Executar o Script

Para executar o script `processamento.py`, siga os passos abaixo:

**1. Pré-requisitos**:

- Tenha o Python instalado na sua máquina.
- Instale as bibliotecas necessárias utilizando `pip`:

```bash
pip install pandas requests openpyxl
```

**2. Arquivos Necessários**:

Certifique-se de ter os arquivos `dados.xlsx` e `sistema.xlsx` na mesma pasta que o script `processamento.py`.

**3. Execução**:

No terminal, navegue até a pasta onde o script está localizado e execute o comando:

```bash
python processamento.py
```

**4. Resultados**:
   
Após a execução, os seguintes arquivos serão gerados:

- `clientes_invalidos.xlsx`: Contém os clientes inválidos e os motivos da invalidação.
- `clientes_para_subir.json`: Contém os dados dos clientes válidos prontos para serem inseridos ou atualizados no sistema.

<br>


## 📜 Logs de Execução

Durante a execução do script, são gerados logs que ajudam a monitorar o processo e identificar possíveis problemas. Abaixo está um exemplo dos logs gerados:

<img src="/logs.png">

Esses logs mostram o progresso das diferentes etapas do processo, desde a padronização dos dados até a geração dos arquivos de saída. Eles são úteis para garantir que o script esteja funcionando corretamente e para diagnosticar quaisquer problemas que possam surgir.

<br>


## 🤝 Considerações Finais

Este script foi desenvolvido para garantir que todos os dados de clientes sejam validados de acordo com as regras estabelecidas e preparados corretamente para inserção ou atualização no sistema. A utilização da API ViaCEP garante a precisão dos endereços. Espero que esta solução atenda às expectativas da Principia e demonstre minhas habilidades em manipulação e validação de dados.

Caso haja qualquer dúvida ou necessidade de ajuste, estou à disposição para auxiliar.