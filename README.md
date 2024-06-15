```markdown
<h1 align='center'>Desafio de Processamento de Dados - Principia 🚀</h1>

<p align="center">
  <img src="https://c5gwmsmjx1.execute-api.us-east-1.amazonaws.com/prod/dados_processo_seletivo/logo_empresa/147549/principia.jpg" alt="Logo Principia">
</p>

O objetivo do desafio foi validar e processar dados de clientes a partir de um arquivo Excel, utilizando diversas regras de validação, e gerar arquivos de saída com os resultados.

<br>

## 📋 Descrição do Desafio

O desafio consistiu nas seguintes etapas:
1. **Validação dos dados de clientes:**
   - O CPF do cliente é válido?
   - O cliente possui nome completo?
   - A data de nascimento é válida?
   - É uma idade possível? (Maiores de 17 anos)
   - O e-mail é válido?
   - O telefone informado está no formato certo?
   - Validar o CEP utilizando a API: [ViaCEP](https://viacep.com.br/)
   - Validar o endereço informado utilizando a API: [ViaCEP](https://viacep.com.br/)
2. **Exportação de dados inválidos para um arquivo Excel (`clientes_invalidos.xlsx`) com o motivo da invalidação.**
3. **Comparação de clientes válidos com um arquivo de sistema (`sistema.xlsx`).**
   - Se o cliente já tiver cadastro, ele receberá o tipo `A` de atualização.
   - Se o cliente não tiver cadastro, ele receberá o tipo `I` de inserção.
4. **Exportação de clientes válidos para um arquivo JSON (`clientes_para_subir.json`).**

<br>

## 🛠 Implementação

A solução foi implementada em um script Python (`processamento.py`) que realiza as seguintes etapas:

### 📚 Importação de Bibliotecas

<details>
  <summary>Código de importação de bibliotecas</summary>

```python
import pandas as pd
import re
import requests
from datetime import datetime
import json
```
</details>

### 🔧 Funções de Padronização e Validação

- **Padronização e limpeza de dados:** Converte texto para maiúsculas, remove espaços em branco, formata CPF e data de nascimento, remove caracteres não numéricos de telefones, padroniza o nome da faculdade e elimina duplicatas.

<details>
  <summary>Código de padronização e limpeza de dados</summary>

```python
def padronizar_e_limpar_dados(df):
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
    df = df.drop_duplicates()
    return df
```
</details>

- **Validação do CPF:** Verifica se o CPF é válido usando dígitos verificadores.

<details>
  <summary>Código de validação do CPF</summary>

```python
def validar_cpf(cpf):
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

- **Validação de e-mail:** Verifica se o e-mail está no formato correto usando expressões regulares.

<details>
  <summary>Código de validação de e-mail</summary>

```python
def validar_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
```
</details>

- **Validação de telefone:** Verifica se o telefone está no formato correto (10 ou 11 dígitos).

<details>
  <summary>Código de validação de telefone</summary>

```python
def validar_telefone(telefone):
    return re.match(r'^\d{10,11}$', str(telefone)) is not None
```
</details>

- **Validação de data de nascimento e idade:** Verifica se a data é válida e se a pessoa tem mais de 17 anos.

<details>
  <summary>Código de validação de data de nascimento e idade</summary>

```python
def validar_data_nascimento(data_nascimento):
    try:
        data = datetime.strptime(data_nascimento, '%Y-%m-%d')
        idade = (datetime.now() - data).days // 365
        return idade >= 18
    except ValueError:
        return False
```
</details>

- **Validação de nome completo:** Verifica se o nome contém pelo menos duas palavras.

<details>
  <summary>Código de validação de nome completo</summary>

```python
def validar_nome_completo(nome):
    return len(nome.split()) >= 2
```
</details>

- **Validação de CEP utilizando a API ViaCEP:** Verifica se o CEP é válido e retorna os dados do endereço.

<details>
  <summary>Código de validação de CEP</summary>

```python
def validar_cep(cep):
    response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    if response.status_code == 200:
        data = response.json()
        if data.get('erro'):
            return False, {}
        return True, data
    return False, {}
```
</details>

- **Validação de endereço utilizando os dados da API ViaCEP:** Verifica se o endereço corresponde ao CEP fornecido.

<details>
  <summary>Código de validação de endereço</summary>

```python
def validar_endereco(data, endereco, bairro, cidade, estado):
    return (data['logradouro'].upper() in endereco and
            data['bairro'].upper() == bairro and
            data['localidade'].upper() == cidade and
            data['uf'].upper() == estado)
```
</details>

### 🧩 Função Principal de Processamento

A função principal carrega os dados, padroniza-os, valida cada registro e exporta os resultados.

<details>
  <summary>Código da função principal de processamento</summary>

```python
def processar_dados():
    # Carregar e padronizar os dados
    caminho_arquivo = 'dados.xlsx'
    df = pd.read_excel(caminho_arquivo)
    df_limpo = padronizar_e_limpar_dados(df)
    print("Dados padronizados.")

    # Validar os dados
    clientes_validos = []
    clientes_invalidos = []

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
    print("Validação concluída. Arquivo 'clientes_invalidos.xlsx' foi gerado.")

    # Comparar com o sistema
    sistema_path = 'sistema.xlsx'
    df_sistema = pd.read_excel(sistema_path)
    df_clientes_validos['CPF'] = df_clientes_validos['CPF'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(11))
    df_sistema['cpf'] = df_sistema['cpf'].apply(lambda x: re