import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=6)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        popup_text = f"""
        <b>ANO:</b> {row.get('ano', '')} |
        <b>BEM:</b> {str(row.get('bem', '')).replace('\n', ' ')} |
        <b>PARLAMENTAR:</b> {str(row.get('parlamentar', '')).replace('\n', ' ')} |
        <b>BENEFICIARIO:</b> {row.get('beneficiario', '')} |
        <b>MUNICIPIO:</b> {row.get('municipio', '')} |
        <b>ENTREGUE:</b> {row.get('entrega_realizada_pelo_fornecedor', '')}
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=450),
            icon=folium.Icon(color='red')
        ).add_to(marker_cluster)

    st_data = st_folium(m, width=1200, height=700)
