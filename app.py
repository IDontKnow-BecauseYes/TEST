import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from io import BytesIO

st.set_page_config(page_title="Mapa de Irrigação", layout="wide")

st.title("Mapa – IRRIGACAO.csv")

# Upload do arquivo
file = st.file_uploader("Envie o arquivo IRRIGACAO.csv", type=["csv"])

if file:
    df = pd.read_csv(file)

    # Normalização básica para evitar erros
    df.columns = df.columns.str.strip()

    # Identifica colunas de latitude e longitude
    col_lat = next((c for c in df.columns if "lat" in c.lower()), None)
    col_lon = next((c for c in df.columns if "lon" in c.lower()), None)

    if not col_lat or not col_lon:
        st.error("Não encontrei colunas de latitude e longitude.")
        st.stop()

    # Filtrar somente coordenadas válidas
    df_valid = df.dropna(subset=[col_lat, col_lon]).copy()

    # Ajustar tipos numéricos
    df_valid[col_lat] = pd.to_numeric(df_valid[col_lat], errors="coerce")
    df_valid[col_lon] = pd.to_numeric(df_valid[col_lon], errors="coerce")
    df_valid = df_valid.dropna(subset=[col_lat, col_lon])

    # Centro do mapa
    lat_med = df_valid[col_lat].mean()
    lon_med = df_valid[col_lon].mean()

    # Criar mapa
    mapa = folium.Map(location=[lat_med, lon_med], zoom_start=7)
    mc = MarkerCluster().add_to(mapa)

    # Ícone de gota (cor azul)
    drop_icon = folium.Icon(color="blue", icon="tint", prefix="fa")

    # Adiciona marcadores
    for _, row in df_valid.iterrows():
        popup_txt = (
            f"<b>Município:</b> {row.get('Mun.', '')}<br>"
            f"<b>Descrição:</b> {row.get('Descrição', '')}<br>"
            f"<b>Quantidade:</b> {row.get('Quantidade', '')}"
        )

        folium.Marker(
            location=[row[col_lat], row[col_lon]],
            popup=popup_txt,
            icon=drop_icon
        ).add_to(mc)

    # Exibe mapa
    folium_static(mapa, width=900, height=600)

    st.subheader("Tabela do Arquivo")
    st.dataframe(df, use_container_width=True)

    # === BOTÕES PARA DOWNLOAD ===
    st.subheader("Downloads")

    col1, col2 = st.columns(2)

    # Download do mapa
    with col1:
        map_html = mapa._repr_html_().encode("utf-8")
        st.download_button(
            "Baixar Mapa (HTML)",
            data=map_html,
            file_name="mapa_irrigacao.html",
            mime="text/html"
        )

    # Download do dataframe
    with col2:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "Baixar Dataframe (XLSX)",
            data=buffer,
            file_name="IRRIGACAO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
