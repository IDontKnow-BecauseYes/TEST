import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("Mapa de Coordenadas")

uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
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
