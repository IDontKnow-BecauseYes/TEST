import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html
from io import BytesIO

st.set_page_config(page_title="Infraestrutura — Mapas e Tabelas", layout="wide")

PATHS = {
    "Antes de 2023": "arquivos/INFRAESTRUTURA_antes_de_2023.xlsx",
    "Depois de 2023": "arquivos/INFRAESTRUTURA_depois_de_2023.xlsx",
    "Total": "arquivos/INFRAESTRUTURA_total.xlsx",
}

@st.cache_data
def read_excel(path):
    try:
        return pd.read_excel(path)
    except Exception:
        return pd.DataFrame()

def find_coord_cols(df):
    lat = [c for c in df.columns if "lat" in c.lower()]
    lon = [c for c in df.columns if "lon" in c.lower() or "long" in c.lower()]
    return lat[0] if lat else None, lon[0] if lon else None

def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


st.title("Infraestrutura — mapas e tabelas")

choice = st.selectbox("Selecionar conjunto", list(PATHS.keys()))

df = read_excel(PATHS[choice])
if df.empty:
    st.stop()

lat_col, lon_col = find_coord_cols(df)
if lat_col:
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
if lon_col:
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')

st.subheader(choice)

with st.expander("Tabela editável", expanded=True):
    try:
        edited = st.data_editor(df, num_rows="dynamic")
    except:
        edited = st.experimental_data_editor(df, num_rows="dynamic")

all_columns = list(edited.columns)
visible_columns = st.multiselect("Colunas visíveis:", all_columns, default=all_columns)

col1, col2 = st.columns([1, 1])

# ---------------------------------------------------------
# MAPA FOLIUM
# ---------------------------------------------------------
with col1:
    st.markdown("**Mapa (Folium)**")

    if lat_col and lon_col:
        points = edited.dropna(subset=[lat_col, lon_col])
        if not points.empty:
            center_lat = points[lat_col].mean()
            center_lon = points[lon_col].mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
            mc = MarkerCluster().add_to(m)

            for _, row in points.iterrows():
                popup_text = "<br>".join(
                    [f"<b>{c}:</b> {row[c]}" for c in visible_columns if c not in [lat_col, lon_col]]
                )
                folium.Marker(
                    [row[lat_col], row[lon_col]],
                    popup=popup_text
                ).add_to(mc)

            html_data = m._repr_html_()
            html(html_data, height=600)
        else:
            st.info("Sem coordenadas válidas no arquivo.")
    else:
        st.info("Arquivo não possui colunas de latitude/longitude.")

# ---------------------------------------------------------
# TABELA + DOWNLOAD
# ---------------------------------------------------------
with col2:
    st.markdown("**Tabela filtrada**")
    st.dataframe(edited[visible_columns])

    csv_bytes = edited[visible_columns].to_csv(index=False).encode("utf-8")
    excel_bytes = to_excel_bytes(edited[visible_columns])

    st.download_button(
        "Baixar CSV (visíveis)",
        csv_bytes,
        file_name=f"{choice.replace(' ', '_').lower()}_visiveis.csv",
        mime="text/csv"
    )

    st.download_button(
        "Baixar XLSX (visíveis)",
        excel_bytes,
        file_name=f"{choice.replace(' ', '_').lower()}_visiveis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

