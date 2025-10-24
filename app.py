import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

pocos_file = st.file_uploader("Upload CSV de Poços", type="csv")
mun_file = st.file_uploader("Upload CSV de Municípios", type="csv")

if pocos_file is not None and mun_file is not None:
    # Leitura dos arquivos
    dfp = pd.read_csv(pocos_file, dtype=str)
    dfm = pd.read_csv(mun_file, dtype=str)

    # Limpeza coordenadas poços
    LAT_COL = "LATITUDE_POCOS"
    LON_COL = "LONGITUDE_POCOS"
    for col in (LAT_COL, LON_COL):
        if col in dfp.columns:
            dfp[col] = pd.to_numeric(
                dfp[col].astype(str).str.replace(",", ".").str.strip().str.replace(r"[^\d\.\-]", "", regex=True),
                errors="coerce"
            )
    valid = dfp.dropna(subset=[LAT_COL, LON_COL]).copy()

    # Mapa folium
    center_lat = valid[LAT_COL].mean() if not valid.empty else 0.0
    center_lon = valid[LON_COL].mean() if not valid.empty else 0.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8 if not valid.empty else 2, control_scale=True)
    marker_cluster = MarkerCluster().add_to(m)

    info_cols = ["PLANILHA", "ORDEM", "CONTRATO", "LOCALIDADES", "DATA_DE_PERFURACAO", "DATA_DE_INTALACAO", "SITUACAO"]
    for _, row in valid.iterrows():
        lat = float(row[LAT_COL])
        lon = float(row[LON_COL])
        popup_lines = []
        for col in info_cols:
            val = str(row.get(col, "")) if not pd.isna(row.get(col, "")) else ""
            popup_lines.append(f"<b>{col}:</b> {val}")
        popup_html = "<br>".join(popup_lines)
        popup = folium.Popup(popup_html, max_width=420)
        plan = row.get("PLANILHA", "")
        tooltip = str(plan).strip() if plan and not pd.isna(plan) else None
        folium.Marker(location=[lat, lon], popup=popup, tooltip=tooltip,
                      icon=folium.Icon(color="red", icon="info-sign")).add_to(marker_cluster)

    # Salvar mapa temporariamente e exibir
    m.save("map_pocos.html")
    html = open("map_pocos.html", "r", encoding="utf-8").read()
    st.components.v1.html(html, height=600)

    # Limpeza coordenadas municípios
    for col in ["LATITUDE_MUNICIPIOS", "LONGITUDE_MUNICIPIOS"]:
        if col in dfm.columns:
            dfm[col] = pd.to_numeric(
                dfm[col].astype(str).str.replace(",", ".").str.strip().str.replace(r"[^\d\.\-]", "", regex=True),
                errors="coerce"
            )

    # Botões para download dos CSVs limpos
    st.download_button("Baixar CSV poços limpo", dfp.to_csv(index=False).encode("utf-8"),
                       file_name="pocos_codevasf_limpo.csv", mime="text/csv")
    st.download_button("Baixar CSV municípios limpo", dfm.to_csv(index=False).encode("utf-8"),
                       file_name="municipio_codevasf_limpo.csv", mime="text/csv")

    # Exibir dataframes
    st.markdown("## DataFrame completo - Poços")
    st.dataframe(dfp, use_container_width=True)
    st.markdown("## DataFrame completo - Municípios")
    st.dataframe(dfm, use_container_width=True)

