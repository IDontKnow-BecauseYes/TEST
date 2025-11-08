import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("Mapa e DataFrames de Poços")

# Upload do arquivo de poços
uploaded_pocos = st.file_uploader("Upload do arquivo de poços (CSV)", type="csv", key="pocos")

if uploaded_pocos is not None:
    # Lê o CSV
    df_pocos = pd.read_csv(uploaded_pocos, dtype=str)

    # Nomes fixos de colunas esperadas
    lat_col = "LATITUDE_POCOS"
    lon_col = "LONGITUDE_POCOS"
    municipio_col = "LOCALIDADES"

    # Converte coordenadas
    df_pocos["_lat"] = pd.to_numeric(df_pocos[lat_col].astype(str).str.replace(",", "."), errors="coerce")
    df_pocos["_lon"] = pd.to_numeric(df_pocos[lon_col].astype(str).str.replace(",", "."), errors="coerce")

    # Filtra linhas válidas
    pontos = df_pocos.dropna(subset=["_lat", "_lon"]).copy()

    # --- Mapa ---
    if len(pontos) > 0:
        centro_lat = pontos["_lat"].mean()
        centro_lon = pontos["_lon"].mean()
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=6)
        cluster = MarkerCluster().add_to(mapa)

        # Adiciona marcadores
        for _, row in pontos.iterrows():
            popup_text = f"""
            <b>Localidade:</b> {row.get('LOCALIDADES', '')}<br>
            <b>Situação:</b> {row.get('SITUACAO', '')}<br>
            <b>Data perfuração:</b> {row.get('DATA_DE_PERFURACAO', '')}<br>
            <b>Data instalação:</b> {row.get('DATA_DE_INSTALACAO', '')}
            """
            folium.Marker(
                location=[row["_lat"], row["_lon"]],
                popup=popup_text,
                icon=folium.Icon(color="blue", icon="tint")
            ).add_to(cluster)

        st.markdown("### 🌍 Mapa de Poços")
        st_folium(mapa, width=1200, height=550)
    else:
        st.warning("Nenhuma coordenada válida encontrada nas colunas LATITUDE_POCOS e LONGITUDE_POCOS.")
        mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)
        st_folium(mapa, width=1200, height=450)

    # --- DataFrame de Poços Individuais (sem lat/lon) ---
    st.markdown("### 🧾 Poços Individuais")
    colunas_remover = [lat_col, lon_col, "_lat", "_lon"]
    df_individual = df_pocos.drop(columns=colunas_remover, errors="ignore")
    st.dataframe(df_individual, use_container_width=True)

    # --- DataFrame de Poços Totais (agrupados por município/localidade) ---
    st.markdown("### 📌 Poços Totais por Município")
    df_totais = (
        df_pocos.groupby(municipio_col)
        .size()
        .reset_index(name="quant_pocos")
        .rename(columns={municipio_col: "municipio"})
        .sort_values("quant_pocos", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(df_totais, use_container_width=True)

    # --- Botões de Download ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇️ Baixar Poços Individuais (CSV)",
            data=df_individual.to_csv(index=False).encode("utf-8"),
            file_name="pocos_individuais.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            "⬇️ Baixar Poços Totais (CSV)",
            data=df_totais.to_csv(index=False).encode("utf-8"),
            file_name="pocos_totais.csv",
            mime="text/csv"
        )

    with col3:
        html_str = mapa.get_root().render()
        st.download_button(
            "⬇️ Baixar Mapa (HTML)",
            data=html_str.encode("utf-8"),
            file_name="mapa_pocos.html",
            mime="text/html"
        )

else:
    st.info("Faça upload do arquivo CSV de poços para gerar o mapa e os DataFrames.")
