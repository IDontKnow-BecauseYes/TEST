import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Mapa e Dados – IRRIGACAO")

# ========================
# UPLOAD DO ARQUIVO
# ========================
arquivo = st.file_uploader("Envie o arquivo IRRIGACAO.csv", type=["csv"])

if arquivo:
    # ========================
    # LEITURA SEGURA DO CSV
    # ========================
    df = pd.read_csv(arquivo, sep=None, engine="python")

    st.write("Colunas encontradas:", df.columns.tolist())

    # ========================
    # DETECTAR LAT/LON
    # ========================
    possiveis_lat = ["latitude", "lat", "Latitude", "LAT", "Lat"]
    possiveis_lon = ["longitude", "lon", "Longitude", "LON", "Long"]

    col_lat = None
    col_lon = None

    for c in df.columns:
        if c in possiveis_lat:
            col_lat = c
        if c in possiveis_lon:
            col_lon = c

    if not col_lat or not col_lon:
        st.error("Não encontrei as colunas de latitude e longitude.")
        st.stop()

    # ========================
    # CRIAR MAPA
    # ========================
    lat_med = df[col_lat].mean()
    lon_med = df[col_lon].mean()

    m = folium.Map(location=[lat_med, lon_med], zoom_start=10)
    mc = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        folium.Marker(
            [row[col_lat], row[col_lon]],
            popup=str(row.to_dict())
        ).add_to(mc)

    st.subheader("Mapa")
    mapa_render = st_folium(m, width=800, height=500)

    # ========================
    # MOSTRAR DATAFRAME
    # ========================
    st.subheader("DataFrame")
    st.dataframe(df)

    # ========================
    # BOTÕES DE DOWNLOAD
    # ========================
    col1, col2 = st.columns(2)

    # Baixar mapa HTML
    with col1:
        html_str = m.get_root().render()
        st.download_button(
            label="Baixar Mapa (HTML)",
            data=html_str,
            file_name="mapa.html",
            mime="text/html"
        )

    # Baixar DataFrame XLSX
    with col2:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="Baixar DataFrame (XLSX)",
            data=buffer,
            file_name="dados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
