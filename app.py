# Streamlit app — Infraestrutura (antes, depois, total)
# Cria 3 caixas (alternador), cada uma com:
# - mapa com marcações (Latitude/Longitude)
# - data editor (editável)
# - seletor de colunas visíveis
# - botão de download que baixa somente as colunas visíveis
# Arquivos usados (já enviados):
# /mnt/data/INFRAESTRUTURA_antes_de_2023.xlsx
# /mnt/data/INFRAESTRUTURA_depois_de_2023.xlsx
# /mnt/data/INFRAESTRUTURA_total.xlsx

import streamlit as st
import pandas as pd
import pydeck as pdk
import io
from io import BytesIO

st.set_page_config(page_title="Infraestrutura — Mapas e Tabelas", layout="wide")

# Paths locais (fornecidos pelo usuário / upload)
PATHS = {
    "Antes de 2023": "/mnt/data/INFRAESTRUTURA_antes_de_2023.xlsx",
    "Depois de 2023": "/mnt/data/INFRAESTRUTURA_depois_de_2023.xlsx",
    "Total": "/mnt/data/INFRAESTRUTURA_total.xlsx",
}

@st.cache_data
def read_excel(path):
    try:
        return pd.read_excel(path)
    except Exception as e:
        st.error(f"Erro ao ler {path}: {e}")
        return pd.DataFrame()


def find_coord_cols(df):
    # procura colunas que contenham lat/lon (case-insensitive)
    cols = {c.lower(): c for c in df.columns}
    lat_candidates = [c for c in df.columns if 'lat' in c.lower()]
    lon_candidates = [c for c in df.columns if 'lon' in c.lower() or 'long' in c.lower()]
    lat_col = lat_candidates[0] if lat_candidates else None
    lon_col = lon_candidates[0] if lon_candidates else None
    return lat_col, lon_col


def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data


st.title("Infraestrutura — mapas e tabelas")
st.write("Escolha um dos conjuntos de dados e trabalhe nos mapas e tabelas. Download baixa apenas as colunas visíveis.")

# Selector: três caixas que alternam entre os arquivos
choice = st.selectbox("Selecionar conjunto", list(PATHS.keys()))

# Carrega
df = read_excel(PATHS[choice])

if df.empty:
    st.stop()

# Detecta colunas de coordenadas
lat_col, lon_col = find_coord_cols(df)
if not lat_col or not lon_col:
    st.warning("Não foi encontrada coluna de Latitude/Longitude automaticamente. Certifique-se de que existam colunas contendo 'lat' e 'lon' no nome.")

# forçar numérico
if lat_col:
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
if lon_col:
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')

# coluna para edição — mostrar todas por padrão
st.sidebar.header("Configurações")
show_index = st.sidebar.checkbox("Mostrar índice na tabela", value=False)

# Data editor (editável) — Streamlit >=1.22 possui st.data_editor
st.subheader(f"{choice}")
with st.expander("Tabela editável", expanded=True):
    # usa data_editor para edição inline
    try:
        edited = st.data_editor(df, num_rows="dynamic")
    except Exception:
        # fallback para st.experimental_data_editor
        edited = st.experimental_data_editor(df, num_rows="dynamic")

# Seleção de colunas visíveis
all_columns = list(edited.columns)
visible_columns = st.multiselect("Colunas visíveis (serão as colunas baixadas):", all_columns, default=all_columns)

# Área do mapa e tabela lado-a-lado
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("**Mapa**")
    # preparar dados para mapa
    map_df = edited.copy()
    if lat_col and lon_col:
        map_points = map_df.dropna(subset=[lat_col, lon_col])
        if not map_points.empty:
            # pydeck exige que as coordenadas sejam [lon, lat]
            midpoint = (map_points[lat_col].mean(), map_points[lon_col].mean())
            # usa ScatterplotLayer
            tooltip_fields = visible_columns[:6] if visible_columns else list(map_points.columns[:6])
            tooltip_html_parts = [f"<b>{col}:</b> {{{col}}}" for col in tooltip_fields if col not in [lat_col, lon_col]]
            tooltip_html = "<br>".join(tooltip_html_parts) if tooltip_html_parts else "{index}"

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_points,
                get_position=f"[{lon_col}, {lat_col}]",
                get_radius=200,
                pickable=True,
                auto_highlight=True,
            )

            tooltip = {"html": tooltip_html}

            view_state = pdk.ViewState(
                longitude=map_points[lon_col].mean(),
                latitude=map_points[lat_col].mean(),
                zoom=10,
                pitch=0,
            )

            r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
            st.pydeck_chart(r)
        else:
            st.info("Não há pontos com coordenadas válidas para mostrar no mapa.")
    else:
        st.info("Colunas de Latitude/Longitude não disponíveis; não é possível gerar mapa.")

with col2:
    st.markdown("**Tabela (apenas colunas visíveis serão baixadas)**")
    display_df = edited.copy()
    if not show_index:
        st.dataframe(display_df[visible_columns] if visible_columns else display_df)
    else:
        st.dataframe(display_df[visible_columns] if visible_columns else display_df)

    # Downloads
    col_download_1, col_download_2 = st.columns(2)
    with col_download_1:
        csv_bytes = (display_df[visible_columns].to_csv(index=False).encode('utf-8')) if visible_columns else display_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Baixar CSV (colunas visíveis)",
                           data=csv_bytes,
                           file_name=f"{choice.replace(' ', '_').lower()}_visiveis.csv",
                           mime='text/csv')
    with col_download_2:
        excel_bytes = to_excel_bytes(display_df[visible_columns]) if visible_columns else to_excel_bytes(display_df)
        st.download_button(label="Baixar XLSX (colunas visíveis)",
                           data=excel_bytes,
                           file_name=f"{choice.replace(' ', '_').lower()}_visiveis.xlsx",
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

st.markdown("---")
st.write("Observações: \n- O mapa usa as colunas que contenham 'lat' e 'lon' no nome.\n- O download inclui somente as colunas que você marcou como visíveis.\n- Se quiser que latitude/longitude também sejam baixadas, marque-as como visíveis.")
