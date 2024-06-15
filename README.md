# Desafio de Processamento de Dados - Principia

Este documento descreve a solução implementada para o desafio de processamento de dados solicitado pela empresa Principia para uma vaga de estágio. O objetivo do desafio foi validar e processar dados de clientes a partir de um arquivo Excel, utilizando diversas regras de validação e APIs, e gerar arquivos de saída com os resultados.

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
    df_sistema['cpf'] = df_sistema['cpf'].apply(lambda x: re.sub(r'\D', '', str(x)).zfill(11))
    df_clientes_validos['TIPO'] = 'I'
    df_clientes_validos.loc[df_clientes_validos['CPF'].isin
(df_sistema['cpf']), 'TIPO'] = 'A'
    print("Comparação concluída.")

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

    print("Conversão concluída. Arquivo 'clientes_para_subir.json' foi gerado.")

if __name__ == "__main__":
    processar_dados()
```
</details>

## 🗂 Estrutura do Código

O script `processamento.py` está dividido em várias seções, cada uma responsável por uma parte específica do processamento de dados:

1. **📚 Importação de Bibliotecas**:
   - Importa bibliotecas necessárias para manipulação de dados (`pandas`), validação (`re`), requisições HTTP (`requests`), manipulação de datas (`datetime`) e manipulação de JSON (`json`).

2. **🔧 Funções de Padronização e Validação**:
   - **`padronizar_e_limpar_dados(df)`**: Padroniza e limpa os dados.
   - **`validar_cpf(cpf)`**: Valida o CPF.
   - **`validar_email(email)`**: Valida o formato do e-mail.
   - **`validar_telefone(telefone)`**: Valida o formato do telefone.
   - **`validar_data_nascimento(data_nascimento)`**: Valida a data de nascimento e a idade.
   - **`validar_nome_completo(nome)`**: Verifica se o nome contém pelo menos duas palavras.
   - **`validar_cep(cep)`**: Valida o CEP usando a API ViaCEP.
   - **`validar_endereco(data, endereco, bairro, cidade, estado)`**: Valida se o endereço corresponde ao CEP.

3. **🧩 Função Principal de Processamento (`processar_dados`)**:
   - Carrega os dados de `dados.xlsx` e `sistema.xlsx`.
   - Padroniza e limpa os dados carregados.
   - Valida os dados de cada cliente, adicionando-os a uma lista de clientes válidos ou inválidos, conforme o caso.
   - Exporta os dados inválidos para `clientes_invalidos.xlsx`.
   - Compara os clientes válidos com os dados de `sistema.xlsx` para definir o tipo (`A` para atualização e `I` para inserção).
   - Converte os dados dos clientes válidos para JSON e exporta para `clientes_para_subir.json`.

## 🏃‍♂️ Como Executar o Script

Para executar o script `processamento.py`, siga os passos abaixo:

1. **Pré-requisitos**:
   - Tenha o Python instalado na sua máquina.
   - Instale as bibliotecas necessárias utilizando `pip`:
     ```bash
     pip install pandas requests openpyxl
     ```

2. **Arquivos Necessários**:
   - Certifique-se de ter os arquivos `dados.xlsx` e `sistema.xlsx` na mesma pasta que o script `processamento.py`.

3. **Execução**:
   - No terminal, navegue até a pasta onde o script está localizado e execute o comando:
     ```bash
     python processamento.py
     ```

4. **Resultados**:
   - Após a execução, os seguintes arquivos serão gerados:
     - `clientes_invalidos.xlsx`: Contém os clientes inválidos e os motivos da invalidação.
     - `clientes_para_subir.json`: Contém os dados dos clientes válidos prontos para serem inseridos ou atualizados no sistema.

## 🤝 Considerações Finais

Este script foi desenvolvido para garantir que todos os dados de clientes sejam validados de acordo com as regras estabelecidas e que sejam preparados corretamente para inserção ou atualização no sistema. A utilização de APIs para validação de CEP e endereços garante a precisão dos dados geográficos. Espero que esta solução atenda às expectativas da Principia e demonstre minhas habilidades em manipulação e validação de dados.

Caso haja qualquer dúvida ou necessidade de ajuste, estarei à disposição para auxiliar.