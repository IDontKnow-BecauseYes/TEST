import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import io

st.set_page_config(layout="wide")
st.title("Mapa com Pinos + DataFrame Abaixo (com download do mapa)")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Upload do arquivo CSV", type="csv")

# Colunas desejadas (opcional)
colunas_desejadas = [
    "of", "empresa", "ano", "bem", "parlamentar", "valor_unit",
    "municipio", "beneficiario", "entrega_realizada_pelo_fornecedor",
    "pagamento", "doacao", "entrega_fisica", "baixa",
    "data_de_entrega", "of_emissao"
]

# Possíveis nomes de colunas de latitude/longitude
POSSIVEIS_LAT = ["lat", "latitude", "LAT", "Latitude", "LATITUDE"]
POSSIVEIS_LON = ["lon", "lng", "longitude", "LONG", "Longitude", "LONGITUDE", "LON"]

def achar_coluna(cols, possiveis):
    for p in possiveis:
        if p in cols:
            return p
    return None

mapa = None  # será criado quando houver coordenadas ou mapa padrão

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, dtype=str)
    cols_existentes = [c for c in colunas_desejadas if c in df.columns]
    df_filtrado = df[cols_existentes].copy() if cols_existentes else df.copy()

    # Detecta colunas de coordenadas
    lat_col = achar_coluna(df.columns, POSSIVEIS_LAT)
    lon_col = achar_coluna(df.columns, POSSIVEIS_LON)

    if lat_col and lon_col:
        # Converte para numérico (tratando vírgulas)
        df_filtrado['_lat'] = pd.to_numeric(df[lat_col].astype(str).str.replace(',', '.'), errors='coerce')
        df_filtrado['_lon'] = pd.to_numeric(df[lon_col].astype(str).str.replace(',', '.'), errors='coerce')
        pontos = df_filtrado.dropna(subset=['_lat', '_lon'])

        if len(pontos) == 0:
            st.warning("As colunas de latitude/longitude foram encontradas, mas não contêm valores válidos.")
        else:
            # Cria mapa com cluster de marcadores
            centro_lat = pontos['_lat'].mean()
            centro_lon = pontos['_lon'].mean()
            mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=5)
            cluster = MarkerCluster().add_to(mapa)

            popup_cols = [c for c in ["empresa", "parlamentar", "municipio", "valor_unit"] if c in df_filtrado.columns]

            for _, row in pontos.iterrows():
                popup_text = "<br>".join([f"<b>{col}:</b> {row[col]}" for col in popup_cols if pd.notna(row[col])])
                folium.Marker(
                    location=[row["_lat"], row["_lon"]],
                    popup=popup_text or "Sem dados",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(cluster)

            st.markdown("### 🌍 Mapa com Pinos")
            st_folium(mapa, width=1200, height=550)

    else:
        # Caso não haja lat/lon
        st.warning("Seu CSV não contém colunas de latitude/longitude reconhecidas (ex.: lat, lon, latitude, longitude).")
        mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)
        st.markdown("### 🌍 Mapa Padrão (sem pinos)")
        st_folium(mapa, width=1200, height=450)

    # Mostra o DataFrame apenas uma vez (abaixo do mapa)
    st.markdown("### 🧾 DataFrame Filtrado")
    st.dataframe(df_filtrado.drop(columns=['_lat', '_lon'], errors='ignore'), use_container_width=True)

    df_exportação = df_filtrado.drop(columns=['_lat', '_lon'], errors='ignore'), use_container_width=True

    # Botão de download do XLSX
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_exportação.to_excel(writer, index=False, sheet_name="Dados")
    buffer.seek(0)

    st.download_button(
        label="Baixar XLSX Filtrado",
        data=buffer,
        file_name="dados_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Botão para baixar o mapa como HTML (aparece só se mapa existir) ---
    if mapa is not None:
        html_str = mapa.get_root().render()  # gera o HTML completo do mapa
        st.download_button(
            label="Baixar mapa (HTML)",
            data=html_str.encode("utf-8"),
            file_name="mapa.html",
            mime="text/html"
        )

else:
    st.info("Faça o upload de um arquivo CSV para gerar o mapa e visualizar os dados.")
