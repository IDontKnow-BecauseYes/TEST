import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(page_title="Mapa de Beneficiários - UES Control", layout="wide")
st.title("📍 Mapa Interativo de Beneficiários - UES Control")

uploaded_file = st.file_uploader("Envie o arquivo CSV:", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if "latitude" not in df.columns or "longitude" not in df.columns:
        st.error("O arquivo precisa conter as colunas 'latitude' e 'longitude'.")
    else:
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=6)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in df.iterrows():
            popup_text = f"""
            <b>ANO:</b> {row.get('ano', '')}<br>
            <b>BEM:</b> {str(row.get('bem', '')).replace('\n', ' ')}<br>
            <b>PARLAMENTAR:</b> {str(row.get('parlamentar', '')).replace('\n', ' ')}<br>
            <b>BENEFICIÁRIO:</b> {row.get('beneficiario', '')}<br>
            <b>MUNICÍPIO:</b> {row.get('municipio', '')}<br>
            <b>ENTREGUE:</b> {row.get('entrega_realizada_pelo_fornecedor', '')}
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=450),
                icon=folium.Icon(color='red')
            ).add_to(marker_cluster)

        st_folium(m, width=1200, height=600)

        mapa_html = BytesIO()
        m.save(mapa_html, close_file=False)
        st.download_button(
            label="⬇️ Baixar mapa HTML",
            data=mapa_html.getvalue(),
            file_name="mapa_cluster.html",
            mime="text/html"
        )

        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Baixar CSV tratado",
            data=csv_bytes,
            file_name="ues-control-tratado.csv",
            mime="text/csv"
        )

        with st.expander("📊 Visualizar dados"):
            st.dataframe(df)
else:
    st.info("👆 Envie um arquivo CSV para gerar o mapa e os botões de download.")
