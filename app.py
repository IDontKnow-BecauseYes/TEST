import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from io import BytesIO

st.set_page_config(page_title="Mapa APECUARIA_CONC", layout="wide")
st.title("Mapa – APECUARIA_CONC.csv")

file = st.file_uploader("Envie o arquivo APECUARIA_CONC.csv", type=["csv"])
if not file:
    st.info("Envie o CSV para gerar o mapa.")
    st.stop()

# Leitura tentando detectar separador/encoding
try:
    df = pd.read_csv(file, sep=None, engine="python")
except Exception:
    file.seek(0)
    df = pd.read_csv(file, encoding="utf-8", engine="python")

# Normalizar nomes
df.columns = df.columns.str.strip()

# Detectar colunas de latitude/longitude robustamente
col_lat = next((c for c in df.columns if c.lower() in ("latitude","lat","y")), None)
col_lon = next((c for c in df.columns if c.lower() in ("longitude","lon","lng","x")), None)
# fallback buscando substrings lat/lon
if not col_lat:
    col_lat = next((c for c in df.columns if "lat" in c.lower()), None)
if not col_lon:
    col_lon = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

if not col_lat or not col_lon:
    st.error("Não encontrei colunas de latitude/longitude no CSV. Verifique os nomes das colunas.")
    st.write("Colunas detectadas:", list(df.columns))
    st.stop()

# Filtrar e converter para numérico
df_valid = df.dropna(subset=[col_lat, col_lon]).copy()
df_valid[col_lat] = pd.to_numeric(df_valid[col_lat], errors="coerce")
df_valid[col_lon] = pd.to_numeric(df_valid[col_lon], errors="coerce")
df_valid = df_valid.dropna(subset=[col_lat, col_lon])

if df_valid.empty:
    st.error("Nenhuma coordenada válida encontrada após a limpeza.")
    st.stop()

# Centro do mapa
lat_med = float(df_valid[col_lat].mean())
lon_med = float(df_valid[col_lon].mean())

# Criar mapa e cluster
mapa = folium.Map(location=[lat_med, lon_med], zoom_start=6)
mc = MarkerCluster().add_to(mapa)

# Função para montar popup (adapte campos se quiser)
def make_popup(row):
    # Campos comuns no arquivo APECUARIA_CONC.csv
    return (
        f"<b>Empresa:</b> {row.get('empresa','')}<br>"
        f"<b>Bem:</b> {row.get('bem','')}<br>"
        f"<b>Quantidade:</b> {row.get('quantidade','')}<br>"
        f"<b>Parlamentar:</b> {row.get('parlamentar','')}<br>"
        f"<b>Valor unit.:</b> {row.get('valor_unit','')}<br>"
        f"<b>Estado / Município:</b> {row.get('estado','')} / {row.get('municipio','')}<br>"
        f"<b>Beneficiário:</b> {row.get('beneficiario','')}<br>"
        f"<b>Doação:</b> {row.get('doacao','')} - {row.get('status_doacao','')}<br>"
        f"<b>Área / Intervenção:</b> {row.get('area','')} / {row.get('intervencao','')}"
    )

# Adiciona marcadores
for _, row in df_valid.iterrows():
    popup_txt = make_popup(row)
    icon = folium.Icon(color="blue", icon="tint", prefix="fa")
    folium.Marker(
        location=[row[col_lat], row[col_lon]],
        popup=popup_txt,
        icon=icon,
    ).add_to(mc)

# Exibir mapa
folium_static(mapa, width=900, height=600)

# Mostrar tabela completa (padrão)
st.subheader("Dados (visualização)")
st.dataframe(df, use_container_width=True)

# Downloads
st.subheader("Downloads")
c1, c2 = st.columns(2)

with c1:
    # Renderiza HTML do mapa para download
    map_html = mapa.get_root().render().encode("utf-8")
    st.download_button(
        "Baixar Mapa (HTML)",
        data=map_html,
        file_name="mapa_apecuaria_conc.html",
        mime="text/html"
    )

with c2:
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
        "Baixar Dados (XLSX)",
        data=buf,
        file_name="APECUARIA_CONC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
