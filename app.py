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
    response = chat.send_message(question, stream=False)
    return response.text

# Função para encontrar a coluna de detentor
def encontrar_coluna_detentor(colunas):
    for col in colunas:
        if 'detentor' in col:
            return col
    return None

# Função de comparação de arquivos
def comparar_arquivos(arquivo_db, arquivo_csv):
    if not arquivo_db or not arquivo_csv:
        st.warning("Por favor, envie ambos os arquivos: .db e .csv.")
        return

    with open("/tmp/temp_db.sqlite", "wb") as f:
        f.write(arquivo_db.read())
    con = sqlite3.connect("/tmp/temp_db.sqlite")

    try:
        df_db = pd.read_sql("SELECT * FROM bens", con)
    except Exception as e:
        st.error(f"Erro ao ler tabela 'bens' do banco: {e}")
        return
    finally:
        con.close()

    df_db.columns = df_db.columns.str.lower().str.strip()

    try:
        df_csv = pd.read_csv(arquivo_csv)
    except Exception as e:
        st.error(f"Erro ao ler arquivo CSV: {e}")
        return

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
        resposta = LLM_Response(user_quest)
        st.markdown("### 💬 Resposta:")
        st.write(resposta)

        if "analise de dados" in resposta.lower():
            opcao = st.radio("Escolha uma opção de análise:", ["Comparação de arquivos", "Outra opção"])
            if opcao == "Comparação de arquivos":
                with st.expander("🔍 Enviar arquivos para Análise de Dados"):
                    arquivo_db = st.file_uploader("📦 Envie o banco de dados (.db):", type=["db"])
                    arquivo_csv = st.file_uploader("📄 Envie o arquivo CSV (.csv):", type=["csv"])
                    if st.button("Comparar arquivos"):
                        comparar_arquivos(arquivo_db, arquivo_csv)

# Upload de arquivos texto (opcional)
st.title('Testando upload de arquivo')
arquivoUpload = st.file_uploader('Upload aqui', type='txt')
