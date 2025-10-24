import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components

pocos_file = "pocos_codevasf_limpo.csv"
mun_file = "municipio_codevasf_limpo.csv"
LAT_COL = "LATITUDE_POCOS"
LON_COL = "LONGITUDE_POCOS"
informacoes = ["PLANILHA", "ORDEM", "CONTRATO", "LOCALIDADES", "DATA_DE_PERFURACAO", "DATA_DE_INTALACAO", "SITUACAO"]
arquivo_html = "map_pocos_A.html"

st.set_page_config(layout="wide")

dfp = pd.read_csv(pocos_file, low_memory=False, dtype=str)
for col in (LAT_COL, LON_COL):
    if col in dfp.columns:
        dfp[col] = pd.to_numeric(dfp[col].astype(str).str.replace(",", ".").str.strip().str.replace(r"[^\d\.\-]", "", regex=True), errors="coerce")

valid = dfp.dropna(subset=[LAT_COL, LON_COL]).copy()
center_lat = valid[LAT_COL].mean() if not valid.empty else 0.0
center_lon = valid[LON_COL].mean() if not valid.empty else 0.0
zoom = 8 if not valid.empty else 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)
marker_cluster = MarkerCluster(options={"spiderfyOnClick": True, "showCoverageOnHover": False, "zoomToBoundsOnClick": True}).add_to(m)

for _, row in valid.iterrows():
    lat = float(row[LAT_COL])
    lon = float(row[LON_COL])
    popup_lines = []
    for col in informacoes:
        val = row.get(col, "")
        if pd.isna(val):
            val = ""
        popup_lines.append(f"<b>{col}:</b> {val}")
    popup_html = "<br>".join(popup_lines)
    popup = folium.Popup(popup_html, max_width=420)
    plan = row.get("PLANILHA", "")
    tooltip = str(plan).strip() if plan and not pd.isna(plan) else None
    folium.Marker(location=[lat, lon], popup=popup, tooltip=tooltip, icon=folium.Icon(color="red", icon="info-sign")).add_to(marker_cluster)

m.save(arquivo_html)

dfm = pd.read_csv(mun_file, low_memory=False, dtype=str)
for col in ["LATITUDE_MUNICIPIOS", "LONGITUDE_MUNICIPIOS"]:
    if col in dfm.columns:
        dfm[col] = pd.to_numeric(dfm[col].astype(str).str.replace(",", ".").str.strip().str.replace(r"[^\d\.\-]", "", regex=True), errors="coerce")

col1, col2 = st.columns([2,1])
with col1:
    html = open(arquivo_html, "r", encoding="utf-8").read()
    components.html(html, height=600)
with col2:
    st.download_button("Baixar CSV poços (limpo)", dfp.to_csv(index=False).encode("utf-8"), file_name="pocos_codevasf_limpo.csv", mime="text/csv")
    st.download_button("Baixar CSV municípios (limpo)", dfm.to_csv(index=False).encode("utf-8"), file_name="municipio_codevasf_limpo.csv", mime="text/csv")
    st.markdown("### Resumo")
    st.write(f"Pontos no CSV (pocos): {len(dfp)}")
    st.write(f"Pontos plotados (coordenadas válidas): {len(valid)}")
    st.write(f"Pontos no CSV (municípios): {len(dfm)}")

st.markdown("## DataFrame completo - Poços")
st.dataframe(dfp, use_container_width=True)

st.markdown("## DataFrame completo - Municípios")
st.dataframe(dfm, use_container_width=True)
