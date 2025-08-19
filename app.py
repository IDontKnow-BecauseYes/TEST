import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Poços Brasil — CODEVASF")

# ---------------------- Helpers ----------------------

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

def make_map(center, zoom=6):
    return folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')

def add_zone_circle(m, lat, lon, count, popup_text=None, scale_factor=1.0):
    base = 300
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

st.title("Visualizador de Poços — CODEVASF")
st.markdown("Faça upload do arquivo `CODEVASF_COORDENADAS.csv` (separador vírgula).")

with st.sidebar.expander("Upload e configurações", expanded=True):
    pocos_file = st.file_uploader("CODEVASF_COORDENADAS.csv", type=['csv'], key='pocos')
    scale_factor = st.slider("Fator de escala de zonas", min_value=0.5, max_value=5.0, value=1.0, step=0.1)

query = st.text_input("Digite o nome de um município (ex: 'Teresina'): ")

if not pocos_file:
    st.warning("Faça upload do arquivo `CODEVASF_COORDENADAS.csv` para prosseguir.")
    st.stop()

# ---------------------- Load CSV ----------------------

try:
    df_pocos = pd.read_csv(pocos_file, sep=',', encoding='latin1')
except Exception as e:
    st.error(f"Erro ao ler o arquivo CSV: {e}")
    st.stop()

# Normalizar nome de município
df_pocos['__mun_norm'] = df_pocos['MUNICIPIO'].astype(str).apply(normalize_name)

# ---------------------- Query handling ----------------------

if query:
    qnorm = normalize_name(query)
    pocos_in_mun = df_pocos[df_pocos['__mun_norm'] == qnorm]

    if not pocos_in_mun.empty:
        st.subheader(f"Município encontrado: {pocos_in_mun.iloc[0]['MUNICIPIO']}")

        # Determinar contagem de poços
        if 'POCOS_DEMANDADOS' in df_pocos.columns and df_pocos['POCOS_DEMANDADOS'].notna().any():
            count = pocos_in_mun['POCOS_DEMANDADOS'].astype(float).sum()
            count_source = "POCOS_DEMANDADOS"
        elif 'POCOS_AUTORIZADOS' in df_pocos.columns and df_pocos['POCOS_AUTORIZADOS'].notna().any():
            count = pocos_in_mun['POCOS_AUTORIZADOS'].astype(float).sum()
            count_source = "POCOS_AUTORIZADOS"
        else:
            count = len(pocos_in_mun)
            count_source = "Número de registros"

        st.metric(label='Número de poços neste município', value=int(count))
        st.caption(f"Fonte do total: {count_source}")

        # Pegar coordenadas médias do município
        if 'LATITUDE' in pocos_in_mun.columns and 'LONGITUDE' in pocos_in_mun.columns:
            try:
                lat = pocos_in_mun['LATITUDE'].astype(float).mean()
                lon = pocos_in_mun['LONGITUDE'].astype(float).mean()
                center = (lat, lon)
                m = make_map(center=center, zoom=10)

                add_zone_circle(
                    m,
                    lat, lon,
                    int(count),
                    popup_text=f"{pocos_in_mun.iloc[0]['MUNICIPIO']} — {int(count)} poços",
                    scale_factor=scale_factor
                )

                # Adicionar poços individuais
                for _, r in pocos_in_mun.iterrows():
                    try:
                        folium.CircleMarker(
                            location=(float(r['LATITUDE']), float(r['LONGITUDE'])),
                            radius=3,
                            color='black',
                            fill=True
                        ).add_to(m)
                    except Exception:
                        pass

                st_folium(m, width=900)

            except Exception:
                st.warning("Coordenadas inválidas ou ausentes para este município.")

        # Mostrar tabela detalhada
        cols_to_show = [
            'NUMERO_EDOC','NOME_SOLICITANTE','POCOS_DEMANDADOS','POCOS_AUTORIZADOS',
            'ORDEM_EXECUCAO_DATA','NUMERO_CONTRATO','EMPRESA_CONTRATADA'
        ]
        cols_existentes = [c for c in cols_to_show if c in pocos_in_mun.columns]
        st.dataframe(pocos_in_mun[cols_existentes], use_container_width=True)

        # Download
        csv = pocos_in_mun[cols_existentes].to_csv(index=False, sep=',', encoding='latin1')
        st.download_button(
            label="Download dos dados detalhados (CSV)",
            data=csv,
            file_name=f"pocos_{pocos_in_mun.iloc[0]['MUNICIPIO']}.csv",
            mime="text/csv"
        )

    else:
        st.warning("Município não encontrado. Verifique o nome e tente novamente.")
else:
    st.info("Digite um município e pressione Enter para visualizar.")
