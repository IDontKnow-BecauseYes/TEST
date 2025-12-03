import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Mapa e Dados – IRRIGACAO")

# ---------------------
# upload
# ---------------------
arquivo = st.file_uploader("Envie o arquivo IRRIGACAO.csv", type=["csv"])

def ler_csv_seguro(uploaded):
    separadores = [",", ";", "\t", "|"]
    for sep in separadores:
        try:
            # reset pointer antes de cada tentativa
            try:
                uploaded.seek(0)
            except Exception:
                pass
            df = pd.read_csv(uploaded, sep=sep)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    # tentativa final mais permissiva
    try:
        try:
            uploaded.seek(0)
        except Exception:
            pass
        df = pd.read_csv(uploaded, engine="python", sep=None)
        return df
    except Exception:
        st.error("Não foi possível ler o CSV. Verifique o arquivo.")
        st.stop()

if arquivo:
    df = ler_csv_seguro(arquivo)

    # limpar nomes de coluna (espaços, aspas estranhas)
    df.columns = [str(c).strip().strip('"').strip("'") for c in df.columns]

    st.write("Colunas encontradas:", df.columns.tolist())

    # possíveis nomes de lat/lon (em lower)
    possiveis_lat = ["latitude", "lat"]
    possiveis_lon = ["longitude", "lon", "long"]

    cols_lower = {c.lower(): c for c in df.columns}

    col_lat = None
    col_lon = None
    for name in possiveis_lat:
        if name in cols_lower:
            col_lat = cols_lower[name]
            break
    for name in possiveis_lon:
        if name in cols_lower:
            col_lon = cols_lower[name]
            break

    if not col_lat or not col_lon:
        st.error("Não encontrei colunas de latitude/longitude. Verifique os nomes das colunas.")
        st.stop()

    # converter lat/lon para numérico: trocar vírgula por ponto, remover espaços/aspas
    df[col_lat] = pd.to_numeric(
        df[col_lat].astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip(),
        errors="coerce",
    )
    df[col_lon] = pd.to_numeric(
        df[col_lon].astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip(),
        errors="coerce",
    )

    # remover linhas sem coordenadas válidas
    total_before = len(df)
    df = df.dropna(subset=[col_lat, col_lon])
    total_after = len(df)
    descartadas = total_before - total_after

    st.info(f"Linhas com coordenadas válidas: {total_after} — descartadas: {descartadas}")

    if total_after == 0:
        st.error("Nenhuma linha contém latitude e longitude válidas após a limpeza.")
        st.stop()

    # criar mapa
    lat_med = df[col_lat].mean()
    lon_med = df[col_lon].mean()

    m = folium.Map(location=[lat_med, lon_med], zoom_start=10)
    mc = MarkerCluster().add_to(m)

    # adicionar marcadores (skip se algo ainda der errado)
    for _, row in df.iterrows():
        try:
            lat = float(row[col_lat])
            lon = float(row[col_lon])
            folium.Marker([lat, lon], popup=str(row.to_dict())).add_to(mc)
        except Exception:
            # ignora linha problemática
            continue

    st.subheader("Mapa")
    st_folium(m, width=800, height=500)

    st.subheader("DataFrame")
    st.dataframe(df)

    # botões lado a lado
    col1, col2 = st.columns(2)

    with col1:
        html_str = m.get_root().render()
        st.download_button(
            label="Baixar Mapa (HTML)",
            data=html_str,
            file_name="mapa.html",
            mime="text/html",
        )

    with col2:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="Baixar DataFrame (XLSX)",
            data=buffer,
            file_name="dados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
