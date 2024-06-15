import pandas as pd
import re
import requests
from datetime import datetime
import json

# Função para padronizar e limpar os dados
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

# Função para validar CPF
# Verifica se o CPF é válido usando dígitos verificadores
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

# Função para validar email
# Verifica se o e-mail está no formato correto usando expressões regulares
def validar_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Função para validar telefone
# Verifica se o telefone está no formato correto (10 ou 11 dígitos)
def validar_telefone(telefone):
    return re.match(r'^\d{10,11}$', str(telefone)) is not None

# Função para validar a data de nascimento e idade
#Verifica se a data é válida e se a pessoa tem mais de 17 anos
def validar_data_nascimento(data_nascimento):
    try:
        data = datetime.strptime(data_nascimento, '%Y-%m-%d')
        idade = (datetime.now() - data).days // 365
        return idade >= 18
    except ValueError:
        return False

# Função para validar nome completo
# Verifica se o nome contém pelo menos duas palavras
def validar_nome_completo(nome):
    return len(nome.split()) >= 2

# Função para validar CEP utilizando a API ViaCEP
# Verifica se o CEP é válido e retorna os dados do endereço
def validar_cep(cep):
    response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    if response.status_code == 200:
        data = response.json()
        if data.get('erro'):
            return False, {}
        return True, data
    return False, {}

# Função para validar endereço utilizando os dados da API ViaCEP
# Verifica se o endereço corresponde ao CEP fornecido
def validar_endereco(data, endereco, bairro, cidade, estado):
    return (data['logradouro'].upper() in endereco and
            data['bairro'].upper() == bairro and
            data['localidade'].upper() == cidade and
            data['uf'].upper() == estado)

# Função principal de processamento
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
    df_clientes_validos.loc[df_clientes_validos['CPF'].isin(df_sistema['cpf']), 'TIPO'] = 'A'
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
