import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import io
import unicodedata

st.set_page_config(layout="wide")
st.title("Mapa e DataFrames de Poços")

# --- Helpers ---
POSSIVEIS_LAT = ["lat", "latitude", "LAT", "Latitude", "LATITUDE", "y", "Y"]
POSSIVEIS_LON = ["lon", "lng", "longitude", "LONG", "Longitude", "LONGITUDE", "x", "X"]
POSSIVEIS_MUN = ["municipio", "município", "municipio_nome", "nome_municipio", "municipality", "city", "cidade"]

def achar_coluna(cols, possiveis):
    for p in possiveis:
        if p in cols:
            return p
    return None

def remover_acentos(s: str) -> str:
    if pd.isna(s):
        return s
    nfkd = unicodedata.normalize('NFKD', str(s))
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

# --- Uploader específico para o arquivo "poços" ---
uploaded_pocos = st.file_uploader("Upload do arquivo de poços (CSV)", type="csv", key="pocos")

if uploaded_pocos is not None:
    # lê o CSV como strings para manter tudo e tratar depois
    df_pocos = pd.read_csv(uploaded_pocos, dtype=str)

    # detecta colunas lat/lon/municipio
    lat_col = achar_coluna(df_pocos.columns, POSSIVEIS_LAT)
    lon_col = achar_coluna(df_pocos.columns, POSSIVEIS_LON)
    municipio_col = achar_coluna(df_pocos.columns, POSSIVEIS_MUN)

    # Faz cópia para exibição e processamento (mantendo o original)
    df_individual = df_pocos.copy()

    # tenta converter lat/lon tratando vírgulas decimais
    mapa = None
    pontos_plotados = 0
    if lat_col and lon_col:
        df_individual["_lat"] = pd.to_numeric(df_individual[lat_col].astype(str).str.replace(",", "."), errors="coerce")
        df_individual["_lon"] = pd.to_numeric(df_individual[lon_col].astype(str).str.replace(",", "."), errors="coerce")
        pontos = df_individual.dropna(subset=["_lat", "_lon"]).copy()

        if len(pontos) > 0:
            centro_lat = pontos["_lat"].mean()
            centro_lon = pontos["_lon"].mean()
            mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=6)
            cluster = MarkerCluster().add_to(mapa)

            # escolher colunas para popup automatico: prioritiza nome/municipio/qualquer col existente
            popup_candidates = [c for c in ["nome", "id", "identificador", municipio_col, "empresa", "parlamentar"] if c in df_individual.columns]
            for _, r in pontos.iterrows():
                popup_lines = []
                for c in popup_candidates:
                    if c and pd.notna(r.get(c, None)):
                        popup_lines.append(f"<b>{c}:</b> {r[c]}")
                if not popup_lines:
                    popup_html = f"{r['_lat']}, {r['_lon']}"
                else:
                    popup_html = "<br>".join(popup_lines)
                folium.Marker(location=[r["_lat"], r["_lon"]], popup=popup_html).add_to(cluster)

            pontos_plotados = len(pontos)
        else:
            st.warning("Foram detectadas colunas de latitude/longitude, mas nenhum valor válido foi encontrado nelas.")
    else:
        st.info("Não foram detectadas colunas de latitude/longitude no arquivo de poços. O mapa padrão será exibido sem pinos.")

    # Se mapa não foi criado com pinos, cria um mapa padrão centrado no Brasil
    if mapa is None:
        mapa = folium.Map(location=[-14.235, -51.9253], zoom_start=4)

    # --- Exibe o mapa ---
    st.markdown("### 🌍 Mapa (usando apenas o arquivo de poços)")
    if pontos_plotados:
        st.write(f"Pontos plotados: {pontos_plotados}")
    st_folium(mapa, width=1200, height=550)

    # --- DataFrame individual (poços) ---
    st.markdown("### 🧾 Poços individuais (DataFrame do arquivo de poços)")
    # remove colunas temporárias se existirem para exibição limpa
    df_exibir = df_individual.drop(columns=["_lat", "_lon"], errors="ignore")
    st.dataframe(df_exibir, use_container_width=True)

    # --- DataFrame agregado por município (poços totais) ---
    st.markdown("### 📌 Poços totais por município")
    if municipio_col:
        # normaliza nome do municipio (strip) antes de agrupar
        df_agg = df_individual[[municipio_col]].copy()
        # padroniza: remove espaços nas pontas e agrupa ignorando diferenças de caixa; mantém acentos originais na coluna final
        df_agg["municipio_norm"] = df_agg[municipio_col].astype(str).str.strip()
        # agrupa e conta
        df_totais = (
            df_agg.groupby("municipio_norm")
                  .size()
                  .reset_index(name="quant_pocos")
                  .rename(columns={"municipio_norm": "municipio"})
                  .sort_values("quant_pocos", ascending=False)
                  .reset_index(drop=True)
        )
        st.dataframe(df_totais, use_container_width=True)
    else:
        st.warning("Não foi encontrada uma coluna de município no CSV. Para gerar 'poços totais' é necessário ter uma coluna de município (ex.: 'municipio' ou 'município').")
        df_totais = pd.DataFrame(columns=["municipio", "quant_pocos"])
        st.dataframe(df_totais, use_container_width=True)

    # --- Botões de download ---
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_individual = df_exibir.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar poços individuais (CSV)",
            data=csv_individual,
            file_name="pocos_individuais.csv",
            mime="text/csv"
        )

    with col2:
        csv_totais = df_totais.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar poços totais (CSV)",
            data=csv_totais,
            file_name="pocos_totais_por_municipio.csv",
            mime="text/csv"
        )

    with col3:
        # botão para baixar o mapa como HTML
        html_str = mapa.get_root().render()
        st.download_button(
            "Baixar mapa (HTML)",
            data=html_str.encode("utf-8"),
            file_name="mapa_pocos.html",
            mime="text/html"
        )

else:
    st.info("Faça upload do arquivo CSV de poços para gerar o mapa e os dataframes.")
