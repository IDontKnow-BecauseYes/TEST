"""
Streamlit app: Poços Brasil (POCOS_CODEVASF)

Usage:
1. Put this file in a GitHub repo or run locally.
2. Install dependencies:
   pip install streamlit pandas geopandas shapely folium streamlit-folium pyproj

Run:
   streamlit run streamlit_pocos_app.py

This app expects three CSVs to be uploaded through the sidebar:
 - CIDADES_BRASIL.csv  -> should contain municipality-level info (columns: nome_municipio, nome_estado, latitude, longitude)
 - ESTADOS_GEO.csv      -> should contain state geometry info. Accepts either:
      * a GeoJSON-like string column (geometry) OR
      * WKT string column (geometry) OR
      * columns with centroid lat/lon (latitude, longitude)
      * column with state name (nome_estado)
 - POCOS_CODEVASF.csv  -> wells data with at least municipality name (nome_municipio) and an optional column indicating number of wells (POCOS_DEMANDADOS or POCOS_AUTORIZADOS)

Behavior:
 - The user types a municipality name or a state name in the text input.
 - If the input matches a municipality -> the app aggregates number of wells in that municipality using the numeric column when available (POCOS_DEMANDADOS preferred, then POCOS_AUTORIZADOS) and draws a focused map showing wells and a circle "zone" whose size scales with number of wells.
 - If the input matches a state -> the app zooms to the state's area and shows all municipalities in that state that have wells, with zone circles sized by well counts.

The code tries to detect common column names (case-insensitive). If no numeric column is found, it falls back to counting records (as before).
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from shapely import wkt
from shapely.geometry import Point, shape
import geopandas as gpd
import json

st.set_page_config(layout="wide", page_title="Poços Brasil — Visualizador")

# ---------------------- Helpers ----------------------

def find_column(df, candidates):
    """Find first matching column from candidates (case-insensitive)."""
    cols = {c.lower(): c for c in df.columns}
    for can in candidates:
        if can.lower() in cols:
            return cols[can.lower()]
    # try contains
    for can in candidates:
        for c in cols:
            if can.lower() in c:
                return cols[c]
    return None


def normalize_name(x):
    if pd.isna(x):
        return ""
    return (
        str(x)
        .strip()
        .lower()
        .replace("ç", "c")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("â", "a")
        .replace("ô", "o")
    )


def detect_geometry_column(df):
    """Detect a geometry column that might be WKT or GeoJSON string."""
    for col in df.columns:
        sample = df[col].dropna().astype(str).head(5)
        if sample.empty:
            continue
        # simple heuristics
        if sample.str.startswith('{').any() or sample.str.startswith('[').any():
            return col, 'geojson'
        # WKT detection
        if sample.str.contains('POINT|POLYGON|MULTIPOLYGON|LINESTRING', regex=True).any():
            return col, 'wkt'
    return None, None


def make_map(center, zoom=6):
    m = folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')
    return m


def add_zone_circle(m, lat, lon, count, popup_text=None, scale_factor=1.0):
    # Size scaling: radius in meters. use sqrt scaling so that doubling wells ~ 1.41x radius
    base = 300  # base radius for one well (meters)
    radius = int(base * (np.sqrt(count)) * scale_factor)
    folium.Circle(
        location=(lat, lon),
        radius=radius,
        color='crimson',
        fill=True,
        fill_opacity=0.35,
        popup=popup_text
    ).add_to(m)

# ---------------------- UI ----------------------

st.title("Visualizador de Poços — Cidades e Estados")
st.markdown("Faça upload dos três arquivos CSV na barra lateral e digite o nome de um município ou estado.")

with st.sidebar.expander("Uploads e configurações", expanded=True):
    cidades_file = st.file_uploader("CIDADES_BRASIL.csv", type=['csv'], key='cidades')
    estados_file = st.file_uploader("ESTADOS_GEO.csv", type=['csv'], key='estados')
    pocos_file = st.file_uploader("POCOS_CODEVASF.csv", type=['csv'], key='pocos')
    scale_factor = st.slider("Fator de escala de zonas", min_value=0.5, max_value=5.0, value=1.0, step=0.1)

query = st.text_input("Digite o nome de município ou estado (ex: 'Teresina' ou 'Piauí'): ")

if not (cidades_file and estados_file and pocos_file):
    st.warning("Faça upload dos três arquivos na barra lateral para prosseguir.")
    st.stop()

# ---------------------- Load CSVs ----------------------

try:
    # usuário informou que o separador é ponto-e-vírgula e arquivos costumam estar em latin1
    df_cidades = pd.read_csv(cidades_file, sep=';', engine='python', encoding='latin1')
    df_estados = pd.read_csv(estados_file, sep=';', engine='python', encoding='latin1')
    df_pocos = pd.read_csv(pocos_file, sep=';', engine='python', encoding='latin1')
except Exception as e:
    st.error(f"Erro ao ler os arquivos CSV: {e}")
    st.stop()

# Normalize column names lookup
# CIDADES: find municipality, state, lat, lon
mun_col = find_column(df_cidades, ['municipio', 'nome_municipio', 'city', 'nome'])
state_col = find_column(df_cidades, ['estado', 'nome_estado', 'state'])
lat_col = find_column(df_cidades, ['lat', 'latitude', 'y'])
lon_col = find_column(df_cidades, ['lon', 'longitude', 'lng', 'x'])

if mun_col is None:
    st.error('Não foi possível identificar a coluna de município em CIDADES_BRASIL.csv. Certifique-se de ter uma coluna com nome do município.')
    st.stop()

# POCOS: find municipality col, lat/lon if any
pocos_mun_col = find_column(df_pocos, ['municipio', 'nome_municipio', 'city', 'nome'])
pocos_lat = find_column(df_pocos, ['lat', 'latitude', 'y'])
pocos_lon = find_column(df_pocos, ['lon', 'longitude', 'lng', 'x'])

if pocos_mun_col is None:
    st.error('Não foi possível identificar a coluna de município em POCOS_CODEVASF.csv. Certifique-se de ter uma coluna com nome do município.')
    st.stop()

# ESTADOS: detect name column and geometry
est_name_col = find_column(df_estados, ['estado', 'nome_estado', 'state', 'nome'])
geom_col, geom_type = detect_geometry_column(df_estados)
est_lat = find_column(df_estados, ['lat', 'latitude', 'y'])
est_lon = find_column(df_estados, ['lon', 'longitude', 'lng', 'x'])

# Prepare normalized name columns for matching
for df, col in [(df_cidades, mun_col), (df_pocos, pocos_mun_col)]:
    df['__mun_norm'] = df[col].astype(str).apply(normalize_name)

if state_col:
    df_cidades['__state_norm'] = df_cidades[state_col].astype(str).apply(normalize_name)

if est_name_col:
    df_estados['__state_norm'] = df_estados[est_name_col].astype(str).apply(normalize_name)

# ---------------------- Aggregate wells correctly ----------------------
# Prefer numeric column POCOS_DEMANDADOS, then POCOS_AUTORIZADOS, then fallback to row counts.
count_col_candidates = [
    'pocos_demandados', 'pocos_demandado', 'pocos_demanda',
    'POCOS_DEMANDADOS', 'POCOS_AUTORIZADOS', 'pocos_autorizados',
    'autorizados', 'qtd_pocos', 'quantidade_pocos', 'quantidade'
]
count_col = find_column(df_pocos, count_col_candidates)

if count_col is not None:
    # try convert to numeric
    df_pocos['_count_numeric'] = pd.to_numeric(df_pocos[count_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0).astype(int)
    pocos_counts = df_pocos.groupby('__mun_norm')['_count_numeric'].sum().reset_index(name='well_count')
    count_source = count_col
else:
    # fallback: count rows per municipality
    pocos_counts = df_pocos.groupby('__mun_norm').size().reset_index(name='well_count')
    count_source = 'rows_count'

# Merge counts into cidades (use normalized)
cidades_merged = df_cidades.merge(pocos_counts, how='left', left_on='__mun_norm', right_on='__mun_norm')
if 'well_count' not in cidades_merged:
    cidades_merged['well_count'] = 0
cidades_merged['well_count'] = cidades_merged['well_count'].fillna(0).astype(int)

# Ensure city centroids
if lat_col is None or lon_col is None:
    st.warning('CIDADES_BRASIL.csv não tem colunas de latitude/longitude detectadas. Alguns mapas podem não centrar corretamente.')

# Make a quick geodataframe for municipalities if lat/lon exist
if lat_col and lon_col:
    cidades_merged['__lat'] = pd.to_numeric(cidades_merged[lat_col], errors='coerce')
    cidades_merged['__lon'] = pd.to_numeric(cidades_merged[lon_col], errors='coerce')
    gdf_mun = gpd.GeoDataFrame(cidades_merged, geometry=gpd.points_from_xy(cidades_merged['__lon'], cidades_merged['__lat']))
else:
    gdf_mun = None

# Prepare estados geodataframe if we can parse geometry
if geom_col and geom_type == 'wkt':
    try:
        df_estados['geometry'] = df_estados[geom_col].apply(wkt.loads)
        gdf_est = gpd.GeoDataFrame(df_estados, geometry='geometry')
    except Exception:
        gdf_est = None
elif geom_col and geom_type == 'geojson':
    # try to parse geojson
    try:
        geometries = df_estados[geom_col].apply(lambda s: shape(json.loads(s)) if isinstance(s, str) else None)
        df_estados['geometry'] = geometries
        gdf_est = gpd.GeoDataFrame(df_estados, geometry='geometry')
    except Exception:
        gdf_est = None
elif est_lat is not None and est_lon is not None:
    df_estados['__lat'] = pd.to_numeric(df_estados[est_lat], errors='coerce')
    df_estados['__lon'] = pd.to_numeric(df_estados[est_lon], errors='coerce')
    gdf_est = gpd.GeoDataFrame(df_estados, geometry=gpd.points_from_xy(df_estados['__lon'], df_estados['__lat']))
else:
    gdf_est = None

# ---------------------- Query handling ----------------------

if query:
    qnorm = normalize_name(query)
    # Prefer municipality match first
    mun_matches = cidades_merged[cidades_merged['__mun_norm'] == qnorm]

    if len(mun_matches) >= 1:
        # Municipality path
        st.subheader(f"Município encontrado: {mun_matches.iloc[0][mun_col]}")
        mun_row = mun_matches.iloc[0]
        count = int(mun_row['well_count'])
        st.metric(label='Número de poços neste município', value=count)
        st.caption(f"Fonte do total: {count_source}")

        # Build focused map
        if not np.isnan(mun_row.get('__lat', np.nan)) and not np.isnan(mun_row.get('__lon', np.nan)):
            center = (mun_row['__lat'], mun_row['__lon'])
            m = make_map(center=center, zoom=12)
            # add city marker
            folium.Marker(location=center, popup=f"{mun_row[mun_col]} — {count} poços").add_to(m)
            # add zone circle
            radius = int(300 * np.sqrt(max(1, count)) * scale_factor)
            folium.Circle(location=center, radius=radius, color='blue', fill=True, fill_opacity=0.2, popup=f"Zona: {count} poços").add_to(m)

            # If pocos file has lat/lon, show individual wells in that municipality
            if pocos_lat and pocos_lon:
                pocos_in_mun = df_pocos[df_pocos['__mun_norm'] == qnorm]
                for _, r in pocos_in_mun.iterrows():
                    try:
                        lat = float(r[pocos_lat])
                        lon = float(r[pocos_lon])
                        folium.CircleMarker(location=(lat, lon), radius=3, color='black', fill=True).add_to(m)
                    except Exception:
                        pass

            st_data = st_folium(m, width=900)
        else:
            st.info('Latitude/longitude do município não disponível. Listando resumo de poços no CSV:')
            st.write(mun_row.to_dict())

    else:
        # try state match
        state_matches = df_estados[df_estados['__state_norm'] == qnorm] if '__state_norm' in df_estados else pd.DataFrame()
        if len(state_matches) >= 1:
            st.subheader(f"Estado encontrado: {state_matches.iloc[0][est_name_col]}")
            state_row = state_matches.iloc[0]

            # Filter municipalities in this state (if cidades has state column)
            if '__state_norm' in cidades_merged.columns:
                in_state = cidades_merged[cidades_merged['__state_norm'] == qnorm]
            else:
                in_state = cidades_merged[cidades_merged[mun_col].astype(str).str.contains('', na=False)]

            # Keep only municipalities with wells
            in_state_with_wells = in_state[in_state['well_count'] > 0]

            st.metric('Municípios com poços neste estado', len(in_state_with_wells))
            st.caption(f"Fonte do total por município: {count_source}")

            # Determine center and zoom
            if gdf_est is not None and '__state_norm' in gdf_est.columns:
                est_geom = gdf_est[gdf_est['__state_norm'] == qnorm]
                if not est_geom.empty:
                    bounds = est_geom.geometry.total_bounds  # minx, miny, maxx, maxy
                    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
                    m = make_map(center=center, zoom=6)
                    # add state polygon if available
                    try:
                        for geom in est_geom.geometry:
                            folium.GeoJson(data=gpd.GeoSeries(geom).__geo_interface__, name='Estado').add_to(m)
                    except Exception:
                        pass
                else:
                    center = ( -15.0, -55.0)
                    m = make_map(center=center, zoom=4)
            else:
                # fallback: center map on mean of municipalities lat/lon if available
                if lat_col and lon_col and not in_state_with_wells.empty:
                    mean_lat = in_state_with_wells['__lat'].mean()
                    mean_lon = in_state_with_wells['__lon'].mean()
                    center = (mean_lat, mean_lon)
                    m = make_map(center=center, zoom=6)
                else:
                    m = make_map(center=(-15.0, -55.0), zoom=4)

            # Add municipality zones
            for _, r in in_state_with_wells.iterrows():
                lat = r.get('__lat', None)
                lon = r.get('__lon', None)
                if pd.notna(lat) and pd.notna(lon):
                    popup = f"{r[mun_col]} — {int(r['well_count'])} poços"
                    add_zone_circle(m, lat, lon, int(r['well_count']), popup_text=popup, scale_factor=scale_factor)
                    folium.Marker(location=(lat, lon), popup=popup).add_to(m)

            st_folium(m, width=1000)

        else:
            st.warning('Nenhum município nem estado claramente identificado com esse nome. Verifique grafia e tente novamente.')

else:
    st.info('Digite um município ou estado e pressione Enter para visualizar.')

# ---------------------- Footer / Export ----------------------

st.markdown('---')
if st.button('Exportar resumo de municípios com poços (CSV)'):
    export_cols = ['__mun_norm', mun_col]
    if state_col:
        export_cols.append(state_col)
    export_cols.append('well_count')
    export_df = cidades_merged[export_cols].copy()
    csv = export_df.to_csv(index=False, sep=';', encoding='latin1')
    st.download_button('Download CSV', data=csv, file_name='municipios_pocos_resumo.csv', mime='text/csv')

st.caption('Feito para uso educacional. Ajuste os nomes de colunas conforme seus arquivos CSV.')
