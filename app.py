import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

url_csv = "https://raw.githubusercontent.com/IDontKnow-BecauseYes/TEST/refs/heads/main/arquivos/ues-control-2025-10-07.csv"

st.title("Mapa de Coordenadas - UES Controle")

df = pd.read_csv(url_csv)

df.columns = df.columns.str.strip().str.lower()

df['latitude'] = pd.to_numeric(df['latitude'].astype(str).str.replace(',', '.'), errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'].astype(str).str.replace(',', '.'), errors='coerce')

df = df.dropna(subset=['latitude', 'longitude'])

if not df.empty:
    lat_centro = df['latitude'].mean()
    lon_centro = df['longitude'].mean()
else:
    lat_centro, lon_centro = 0, 0

m = folium.Map(location=[lat_centro, lon_centro], zoom_start=6)

marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    popup_text = f"""
    <b>CONTRATO:</b> {row.get('contrato', '')}<br>
    <b>EMPRESA:</b> {row.get('empresa', '')}<br>
    <b>ANO:</b> {row.get('ano', '')}
    """
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color='red')
    ).add_to(marker_cluster)

st_folium(m, width=700, height=500)
