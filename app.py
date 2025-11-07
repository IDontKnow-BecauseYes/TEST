import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("Visualização de Dados Filtrados")

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
    # Leitura do CSV
    df = pd.read_csv(uploaded_file, dtype=str)

    # Verifica quais colunas existem no arquivo
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]

    if colunas_existentes:
        # Filtra apenas as colunas desejadas existentes
        df_filtrado = df[colunas_existentes].copy()

        st.markdown("### DataFrame Filtrado")
        st.dataframe(df_filtrado, use_container_width=True)

        # Botão para download do CSV filtrado
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
