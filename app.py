import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("Mapa com Pinos + DataFrame Abaixo")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Upload do arquivo CSV", type="csv")

# Colunas que queremos manter (opcional)
colunas_desejadas = [
    "of", "empresa", "ano", "bem", "parlamentar", "valor_unit",
    "municipio", "beneficiario", "entrega_realizada_pelo_fornecedor",
    "pagamento", "doacao", "entrega_fisica", "baixa",
    "data_de_entrega", "of_emissao"
]

# Possíveis nomes de colunas de latitude/longitude
POSSIVEIS_LAT = ["lat", "latitude", "LAT", "Latitude", "LATITUDE"]
POSSIVEIS_LON = ["lon", "lng", "longitude", "LONG", "Longitude", "LONGITUDE", "LON"]

def achar_coluna(cols, possiveis):
    for p in possiveis:
        if p in cols:
            return p
    return None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, dtype=str)
    cols_existentes = [c for c in colunas_desejadas if c in df.columns]
    # Se não encontrar nenhuma das colunas desejadas, ainda mostramos todas as colunas do CSV
    df_filtrado = df[cols_existentes].copy() if cols_existentes else df.copy()

    st.markdown("### 📊 Preview (DataFrame filtrado)")
    st.dataframe(df_filtrado.head(50), use_container_width=True)  # só preview aqui

    # Procura colunas de coordenadas
    lat_col = achar_coluna(df.columns, POSSIVEIS_LAT)
    lon_col = achar_coluna(df.columns, POSSIVEIS_LON)

    if lat_col and lon_col:
        # Converte para numérico (trata vírgula decimal)
        df_filtrado['_lat_raw'] = df[lat_col].astype(str).str.replace(',', '.')
        df_filtrado['_lon_raw'] = df[lon_col].astype(str).str.replace(',', '.')
        df_filtrado['_lat'] = pd.to_numeric(df_filtrado['_lat_raw'], errors='coerce')
        df_filtrado['_lon'] = pd.to_numeric(df_filtrado['_lon_raw'], errors='coerce')

        pontos = df_filtrado.dropna(subset=['_lat', '_lon']).copy()

        n_total = len(pontos)
        if n_total == 0:
            st.warning("Foram encontradas colunas de latitude/longitude, mas nenhum valor válido. Verifique o formato dos números.")
        else:
            # se houver muitos pontos, amostra para evitar travar o navegador
            LIMITE_PONTOS = 5000
            if n_total > LIMITE_PONTOS:
                st.warning(f"Foram detectados {n_total} pontos. Para evitar travamentos, serão plotados {LIMITE_PONTOS} pontos amostrados aleatoriamente.")
                pontos = pontos.sample(LIMITE_PONTOS, random_state=42)

            # Escolha de colunas para mostrar no popup
            popup_defaults = [c for c in ["empresa", "parlamentar", "valor_unit", "municipio"] if c in df_filtrado.columns]
            popup_cols = st.multiselect("Colunas para mostrar no popup (marcadores):", options=list(df_filtrado.columns), default=popup_defaults[:3])

            # Calcula centro do mapa
            centro_lat = pontos['_lat'].mean()
            centro_lon = pontos['_lon'].mean()
            mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=5)

            cluster = MarkerCluster().add_to(mapa)

            for _, row in pontos.iterrows():
                lat = float(row['_lat'])
                lon = float(row['_lon'])
                # monta popup com as colunas selecionadas
                popup_lines = []
                for c in popup_cols:
                    val = row.get(c, "")
                    if pd.isna(val):
                        val = ""
                    popup_lines.append(f"<b>{c}:</b> {val}")
                popup_html = "<br>".join(popup_lines) if popup_lines else f"{lat}, {lon}"
                folium.Marker(location=[lat, lon], popup=popup_html).add_to(cluster)

            st.markdown("### 🌍 Mapa com pinos")
            st.write(f"{len(pontos)} pontos plotados.")
            st_folium(mapa, width=1200, height=550)

            # mostra o dataframe completo (ou filtrado)
            st.markdown("### 🧾 DataFrame Completo / Filtrado")
            st.dataframe(df_filtrado.drop(columns=['_lat_raw','_lon_raw','_lat','_lon'], errors='ignore'), use_container_width=True)

            st.download_button(
                "Baixar CSV",
                data=df_filtrado.to_csv(index=False).encode("utf-8"),
                file_name="dados_com_coordenadas.csv",
                mime="text/csv"
            )
    else:
        # Sem colunas lat/lon encontradas: instruções ao usuário
        st.markdown("### ⚠️ Sem colunas de latitude/longitude encontradas")
        st.warning(
            "Seu CSV não tem colunas de latitude/longitude reconhecidas. "
            "Para que o app desenhe pinos no mapa, inclua no CSV duas colunas com coordenadas (ex.: 'latitude' e 'longitude' ou 'lat' e 'lon').\n\n"
            "Se você já tem nomes diferentes para as colunas de coordenadas, renomeie-as para 'latitude' e 'longitude' ou 'lat' e 'lon'."
        )
        # Exibe mapa padrão (sem pinos) e dataframe completo abaixo
        mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)
        st.markdown("### 🌍 Mapa padrão (sem pinos)")
        st_folium(mapa, width=1200, height=450)

        st.markdown("### 🧾 DataFrame Completo")
        st.dataframe(df_filtrado, use_container_width=True)

        st.download_button(
            "Baixar CSV filtrado",
            data=df_filtrado.to_csv(index=False).encode("utf-8"),
            file_name="dados_filtrados.csv",
            mime="text/csv"
        )
else:
    st.info("Faça upload do CSV para gerar o mapa com pinos (se houver lat/lon) e visualizar o DataFrame.")
