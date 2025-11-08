import streamlit as st
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("Visualização de Dados Filtrados com Mapa")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Upload do arquivo CSV", type="csv")

# Colunas que devem ser exibidas
colunas_desejadas = [
    "of", "empresa", "ano", "bem", "parlamentar", "valor_unit",
    "municipio", "beneficiario", "entrega_realizada_pelo_fornecedor",
    "pagamento", "doacao", "entrega_fisica", "baixa",
    "data_de_entrega", "of_emissao"
]

if uploaded_file is not None:
    # Leitura do CSV
    df = pd.read_csv(uploaded_file, dtype=str)

    # Verifica quais colunas existem no arquivo
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]

    if colunas_existentes:
        # Filtra apenas as colunas desejadas existentes
        df_filtrado = df[colunas_existentes].copy()

        # Mapa interativo (usando a coluna "municipio")
        if "municipio" in df_filtrado.columns:
            st.markdown("### 🌍 Mapa de Municípios")

            geolocator = Nominatim(user_agent="streamlit_app")
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

            # Obtem coordenadas (cacheadas para evitar lentidão)
            @st.cache_data
            def obter_coordenadas(municipios):
                coords = []
                for municipio in municipios:
                    try:
                        loc = geocode(municipio + ", Brasil")
                        if loc:
                            coords.append((municipio, loc.latitude, loc.longitude))
                        else:
                            coords.append((municipio, None, None))
                    except:
                        coords.append((municipio, None, None))
                return pd.DataFrame(coords, columns=["municipio", "lat", "lon"])

            coords_df = obter_coordenadas(df_filtrado["municipio"].dropna().unique())

            # Junta coordenadas ao dataframe original
            df_mapa = df_filtrado.merge(coords_df, on="municipio", how="left")

            # Cria o mapa
            mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)

            # Adiciona marcadores
            for _, row in df_mapa.dropna(subset=["lat", "lon"]).iterrows():
                popup_text = f"<b>{row['municipio']}</b><br>{row.get('empresa', '')}"
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=popup_text,
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(mapa)

            # Exibe o mapa
            st_folium(mapa, width=1200, height=500)

        # Exibe o DataFrame
        st.markdown("### 🧾 DataFrame Filtrado")
        st.dataframe(df_filtrado, use_container_width=True)

        # Botão para download do CSV filtrado
        st.download_button(
            label="Baixar CSV Filtrado",
            data=df_filtrado.to_csv(index=False).encode("utf-8"),
            file_name="dados_filtrados.csv",
            mime="text/csv"
        )
    else:
        st.warning("Nenhuma das colunas especificadas foi encontrada no arquivo CSV.")
else:
    st.info("Por favor, faça o upload de um arquivo CSV para visualizar os dados.")
