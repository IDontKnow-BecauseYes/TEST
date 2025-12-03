import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(layout="wide")

st.title("Mapa e Dados – IRRIGACAO")

# --- Carregar arquivo ---
df = st.file_uploader("Envie o arquivo IRRIGACAO.csv", type=["csv"])

# --- Criar mapa ---
possiveis_lat = ["latitude", "lat", "Latitude", "LAT", "Latitude_GRAUS"]
possiveis_lon = ["longitude", "lon", "Longitude", "LON", "Longitude_GRAUS"]

col_lat = next((c for c in df.columns if c in possiveis_lat), None)
col_lon = next((c for c in df.columns if c in possiveis_lon), None)

if not col_lat or not col_lon:
    st.error("As colunas de latitude e longitude não foram encontradas.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

lat_med = df[col_lat].mean()
lon_med = df[col_lon].mean()

m = folium.Map(location=[lat_med, lon_med], zoom_start=10)
mc = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    folium.Marker(
        [row[col_lat], row[col_lon]],
        popup=str(row.to_dict())
    ).add_to(mc)

# Renderizar
st.subheader("Mapa")
map_data = st_folium(m, width=800, height=500)

# --- Mostrar DataFrame ---
st.subheader("DataFrame")
st.dataframe(df)

# --- Botões lado a lado ---
col1, col2 = st.columns(2)

with col1:
    # Exportar HTML
    html_str = m.get_root().render()
    col1.download_button(
        label="Baixar Mapa (HTML)",
        data=html_str,
        file_name="mapa.html",
        mime="text/html"
    )

with col2:
    # Exportar XLSX
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    col2.download_button(
        label="Baixar DataFrame (XLSX)",
        data=buffer,
        file_name="dados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


