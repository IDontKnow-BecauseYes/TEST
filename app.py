#import streamlit as st
#import pandas as pd
#import folium
#from folium.plugins import MarkerCluster
#from streamlit_folium import st_folium

#url_csv = "https://raw.githubusercontent.com/IDontKnow-BecauseYes/TEST/refs/heads/main/arquivos/ues-control-2025-10-07.csv"

#st.title("Mapa de Coordenadas - UES Controle")

#df = pd.read_csv(url_csv)

#df.columns = df.columns.str.strip().str.lower()

#df['latitude'] = pd.to_numeric(df['latitude'].astype(str).str.replace(',', '.'), errors='coerce')
#df['longitude'] = pd.to_numeric(df['longitude'].astype(str).str.replace(',', '.'), errors='coerce')

#df = df.dropna(subset=['latitude', 'longitude'])

#if not df.empty:
#    lat_centro = df['latitude'].mean()
#    lon_centro = df['longitude'].mean()
#else:
#    lat_centro, lon_centro = 0, 0

#m = folium.Map(location=[lat_centro, lon_centro], zoom_start=6)

#marker_cluster = MarkerCluster().add_to(m)

#for _, row in df.iterrows():
#    popup_text = f"""
#    <b>CONTRATO:</b> {row.get('contrato', '')}<br>
#    <b>EMPRESA:</b> {row.get('empresa', '')}<br>
#    <b>ANO:</b> {row.get('ano', '')}
#    """
#    folium.Marker(
#        location=[row['latitude'], row['longitude']],
#        popup=popup_text,
#        icon=folium.Icon(color='red')
#    ).add_to(marker_cluster)

#st_folium(m, width=700, height=500)
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("Mapa de Coordenadas - UES Controle")

arquivo = st.file_uploader("Envie o arquivo CSV (ues-control-limpo.csv)", type=["csv"])

if arquivo is not None:
    df = pd.read_csv(arquivo)

    if 'latitude' in df.columns and 'longitude' in df.columns:

        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=6)

        for _, row in df.iterrows():
            popup_text = f"""
            <b>ANO:</b> {row.get('ano', '')} |
            <b>BEM:</b> {str(row.get('bem', '')).replace('\n', ' ')} |
            <b>PARLAMENTAR:</b> {str(row.get('parlamentar', '')).replace('\n', ' ')} |
            <b>BENEFICIÁRIO:</b> {row.get('beneficiario', '')} |
            <b>MUNICÍPIO:</b> {row.get('municipio', '')} |
            <b>ENTREGUE:</b> {row.get('entrega_realizada_pelo_fornecedor', '')}
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=450),
                icon=folium.Icon(color='red')
            ).add_to(m)

        st_folium(m, width=800, height=600)
    else:
        st.error("O arquivo CSV deve conter as colunas 'latitude' e 'longitude'.")
else:
    st.info("Envie o arquivo CSV para visualizar o mapa.")
