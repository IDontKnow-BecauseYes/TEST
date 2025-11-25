import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import io

st.set_page_config(layout="wide")
st.title("Mapa — INFRAESTRUTURA_total")

# Caminho fixo do arquivo
FILE_PATH = "arquivos/INFRAESTRUTURA_total.xlsx"

# ---------------------------------------------------------
# LER O ARQUIVO
# ---------------------------------------------------------
try:
    df = pd.read_excel(FILE_PATH, dtype=str)
except:
    st.error("Erro ao carregar INFRAESTRUTURA_total.xlsx")
    st.stop()

# Normalizar nomes de colunas
df.columns = df.columns.str.strip().str.lower()

# Possíveis nomes de latitude/longitude
POSSIVEIS_LAT = ["lat", "latitude", "coord_lat", "coordenada_lat"]
POSSIVEIS_LON = ["lon", "longitude", "lng", "coord_lon", "coordenada_lon"]

def achar_coluna(cols, possiveis):
    for p in possiveis:
        if p in cols:
            return p
    return None

lat_col = achar_coluna(df.columns, POSSIVEIS_LAT)
lon_col = achar_coluna(df.columns, POSSIVEIS_LON)

# ---------------------------------------------------------
# MAPA
# ---------------------------------------------------------
if lat_col and lon_col:
    df["_lat"] = pd.to_numeric(df[lat_col].astype(str).str.replace(",", "."), errors="coerce")
    df["_lon"] = pd.to_numeric(df[lon_col].astype(str).str.replace(",", "."), errors="coerce")

    pontos = df.dropna(subset=["_lat", "_lon"])

    if not pontos.empty:
        centro_lat = pontos["_lat"].mean()
        centro_lon = pontos["_lon"].mean()
    else:
        centro_lat, centro_lon = 0, 0

    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=6)
    cluster = MarkerCluster().add_to(mapa)

    popup_cols = ["id", "municipios"]

    for _, row in pontos.iterrows():
        popup_text = "<br>".join(
            [f"<b>{col.upper()}:</b> {row[col]}" for col in popup_cols if pd.notna(row[col])]
        )

        folium.Marker(
            location=[row["_lat"], row["_lon"]],
            popup=popup_text or "Sem dados",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(cluster)

    st.markdown("### 🌍 Mapa — INFRAESTRUTURA_total")
    st_folium(mapa, width=1200, height=550)

else:
    st.warning("O arquivo não possui colunas de latitude/longitude reconhecidas.")
    mapa = None

# ---------------------------------------------------------
# DATAFRAME
# ---------------------------------------------------------
st.markdown("### 🧾 Tabela Completa — INFRAESTRUTURA_total")
st.dataframe(df.drop(columns=["_lat", "_lon"], errors="ignore"), use_container_width=True)

# ---------------------------------------------------------
# DOWNLOADS
# ---------------------------------------------------------
df_exporta = df.drop(columns=["_lat", "_lon"], errors="ignore")

# XLSX
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_exporta.to_excel(writer, index=False, sheet_name="Dados")
buffer.seek(0)

st.download_button(
    "Baixar XLSX",
    buffer,
    file_name="INFRAESTRUTURA_total.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# HTML do mapa
if mapa:
    html_mapa = mapa.get_root().render()
    st.download_button(
        "Baixar mapa em HTML",
        html_mapa.encode("utf-8"),
        file_name="mapa_infraestrutura_total.html",
        mime="text/html"
    )


