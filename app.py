import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(layout="wide")

st.title("Mapa e Dados – IRRIGACAO")

# --- Carregar arquivo ---
df = pd.read_csv("IRRIGACAO.csv")

# --- Criar mapa ---
lat_med = df["latitude"].mean()
lon_med = df["longitude"].mean()

m = folium.Map(location=[lat_med, lon_med], zoom_start=10)
mc = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
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
