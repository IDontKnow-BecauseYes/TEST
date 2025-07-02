import os
import streamlit as st
from io import StringIO
import google.generativeai as ggi
import pandas as pd
import sqlite3

# Configura a API key do Gemini
ggi.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Inicializa o modelo
model = ggi.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat()

# Função para enviar pergunta ao Gemini
def LLM_Response(question):
    response = chat.send_message(question, stream=True)
    return response

# Função para encontrar a coluna de detentor
def encontrar_coluna_detentor(colunas):
    for col in colunas:
        if 'detentor' in col:
            return col
    return None

# Função de comparação de arquivos
def comparar_arquivos():
    caminho_db = '/content/deposito7grauti (3).db'
    caminho_csv = '/content/bens7sr2025 (2).csv'

    con = sqlite3.connect(caminho_db)
    df_db = pd.read_sql("SELECT * FROM bens", con)
    con.close()
    df_db.columns = df_db.columns.str.lower().str.strip()

    df_csv = pd.read_csv(caminho_csv, sep=None, engine='python')
    df_csv.columns = df_csv.columns.str.lower().str.strip()

    if 'tombamento' not in df_db.columns or 'tombamento' not in df_csv.columns:
        st.error("A coluna 'tombamento' não foi encontrada em um dos arquivos.")
        return

    coluna_detentor_db = encontrar_coluna_detentor(df_db.columns)
    coluna_detentor_csv = encontrar_coluna_detentor(df_csv.columns)

    if not coluna_detentor_db or not coluna_detentor_csv:
        st.error("Não foi possível identificar a coluna de 'detentor' nos arquivos.")
        return

    df_db_filtrado = df_db[["tombamento", coluna_detentor_db]].drop_duplicates()
    df_csv_filtrado = df_csv[["tombamento", coluna_detentor_csv]].drop_duplicates()

    intersecao = pd.merge(df_db_filtrado, df_csv_filtrado, on="tombamento", how="inner", suffixes=("_db", "_csv"))
    divergentes = intersecao[intersecao[f'{coluna_detentor_db}_db'] != intersecao[f'{coluna_detentor_csv}_csv']]

    tabela_nova = pd.DataFrame({
        'Tombamento': divergentes['tombamento'],
        'Arq_Adiminstração': divergentes[f'{coluna_detentor_db}_db'],
        'Arq_7grauTI': divergentes[f'{coluna_detentor_csv}_csv']
    })

    st.markdown("### 🔍 Resultado da Comparação")
    st.dataframe(tabela_nova)

# Configuração básica da página
st.set_page_config(page_title="Chat com Gemini", layout="centered")

# Título
st.title("Chat Aplicação usando Gemini key!")

# Campo de entrada
user_quest = st.text_input("Digite sua pergunta aqui:", placeholder="Ex: Qual a capital da Noruega?")

# Botão
btn = st.button("Resposta")

# Verifica e responde
if btn and user_quest:
    with st.spinner("Pensando..."):
        resposta = ""
        for word in LLM_Response(user_quest):
            resposta += word.text
        st.markdown("### 💬 Resposta:")
        st.write(resposta)

        if "analise de dados" in resposta.lower():
            opcao = st.radio("Escolha uma opção de análise:", ["Comparação de arquivos", "Outra opção"])
            if opcao == "Comparação de arquivos":
                comparar_arquivos()

# Upload de arquivos
st.title('Testando upload de arquivo')
arquivoUpload = st.file_uploader('Upload aqui', type='txt')
