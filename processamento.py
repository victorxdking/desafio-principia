import pandas as pd
import re
import requests
from datetime import datetime
import json
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Função para validar CPF
def validar_cpf(cpf):
    """
    Valida o CPF.
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

# Função para validar email
def validar_email(email):
    """
    Valida o email.
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Função para validar telefone
def validar_telefone(telefone):
    """
    Valida o telefone.
    """
    return re.match(r'^\d{10,11}$', str(telefone)) is not None

# Função para validar a data de nascimento e idade
def validar_data_nascimento(data_nascimento):
    """
    Valida a data de nascimento e verifica se a idade é maior ou igual a 18 anos.
    """
    try:
        data = datetime.strptime(data_nascimento, '%Y-%m-%d')
        idade = (datetime.now() - data).days // 365
        return idade >= 18
    except ValueError:
        return False

# Função para validar nome completo
def validar_nome_completo(nome):
    """
    Verifica se o nome é composto por pelo menos duas palavras.
    """
    return len(nome.split()) >= 2

# Função para validar CEP utilizando a API ViaCEP
def validar_cep(cep):
    """
    Valida o CEP utilizando a API ViaCEP.
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

# Função para validar endereço utilizando os dados da API ViaCEP
def validar_endereco(data, endereco, bairro, cidade, estado):
    """
    Valida o endereço com base nos dados retornados pela API ViaCEP.
    """
    return (data.get('logradouro', '').upper() in endereco and
            data.get('bairro', '').upper() == bairro and
            data.get('localidade', '').upper() == cidade and
            data.get('uf', '').upper() == estado)

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

                   
