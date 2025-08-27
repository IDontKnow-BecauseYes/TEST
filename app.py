import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

url_csv = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPOSITORIO/main/arquivos/coordenadas_convertidas.csv"

st.title("Mapa de Coordenadas")

df = pd.read_csv(url_csv)
coordenadas_validas = df.dropna(subset=["LAT_DECIMAL", "LONG_DECIMAL"])

if not coordenadas_validas.empty:
    lat_centro = coordenadas_validas["LAT_DECIMAL"].mean()
    lon_centro = coordenadas_validas["LONG_DECIMAL"].mean()
else:
    lat_centro, lon_centro = 0, 0

mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=5)

for idx, row in coordenadas_validas.iterrows():
    info_html = "<br>".join([f"<b>{col}:</b> {row[col]}" for col in row.index])
    folium.Marker(
        location=[row["LAT_DECIMAL"], row["LONG_DECIMAL"]],
        popup=folium.Popup(info_html, max_width=300)
    ).add_to(mapa)

st_folium(mapa, width=700, height=500)
