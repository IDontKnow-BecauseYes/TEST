import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Visualização de Dados Filtrados com Mapa")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Upload do arquivo CSV", type="csv")

# Colunas que devem ser exibidas
colunas_desejadas = [
    "of", "empresa", "ano", "bem", "parlamentar", "valor_unit",
    "municipio", "beneficiario", "entrega_realizada_pelo_fornecedor",
    "pagamento", "doacao", "entrega_fisica", "baixa",
    "data_de_entrega", "of_emissao"
]

if uploaded_file is not None:
    # Lê o CSV
    df = pd.read_csv(uploaded_file, dtype=str)

    # Verifica colunas existentes
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]

    if colunas_existentes:
        # Filtra apenas as colunas desejadas
        df_filtrado = df[colunas_existentes].copy()

        # --- Mapa fixo (sem geocoding) ---
        st.markdown("### 🌍 Mapa Interativo (Padrão)")
        mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)  # Centro do Brasil
        st_folium(mapa, width=1200, height=500)

        # --- DataFrame abaixo do mapa ---
        st.markdown("### 🧾 DataFrame Filtrado")
        st.dataframe(df_filtrado, use_container_width=True)

        # Botão de download
        st.download_button(
            label="Baixar CSV Filtrado",
            data=df_filtrado.to_csv(index=False).encode("utf-8"),
            file_name="dados_filtrados.csv",
            mime="text/csv"
        )
    else:
        st.warning("Nenhuma das colunas especificadas foi encontrada no arquivo CSV.")
else:
    st.info("Por favor, faça o upload de um arquivo CSV para visualizar os dados.")
