import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import google.generativeai as genai
from io import StringIO
import os
from dotenv import load_dotenv
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Mapa Interativo com IA",
    page_icon="🗺️",
    layout="wide"
)

# Título principal
#st.title("🗺️ Gerador de Mapas Interativos com IA")
#st.markdown("**Carregue um CSV com dados de localização e converse com a IA sobre seus dados!**")

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configura a chave da API do Gemini
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    st.error("Chave da API GEMINI_API_KEY não encontrada. Certifique-se de que está definida no seu arquivo .env ou como uma variável de ambiente.")
    st.stop() # Interrompe a execução do Streamlit
api_key=GEMINI_API_KEY
genai.configure(api_key=api_key)

# Upload do arquivo CSV
uploaded_file = Path('data/pocos_localizacao.csv')

# Configurações do mapa
map_style = "OpenStreetMap"
marker_color = "#FF0000"

# Inicializar session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'df' not in st.session_state:
    st.session_state.df = None

# Processamento do arquivo CSV
if uploaded_file is not None:
    try:
        # Ler o CSV
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        
        # Criar duas colunas
        col1, col2 = st.columns([3, 1])

        lat_col = "LATITUDE_POCOS"
        lon_col = "LONGITUDE_POCOS"
        label_col = "CIDADE"
        
        with col1:
            st.subheader("🗺️ Localização dos Poços")
            
            # Criar o mapa
            if lat_col and lon_col:
                # Calcular centro do mapa
                center_lat = df[lat_col].mean()
                center_lon = df[lon_col].mean()
                
                # Mapear estilos
                tile_mapping = {
                    "OpenStreetMap": "OpenStreetMap",
                    "CartoDB Positron": "CartoDB positron",
                    "CartoDB Dark_Matter": "CartoDB dark_matter",
                    "Stamen Terrain": "Stamen Terrain"
                }
                
                # Criar mapa base
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=10, #10
                    tiles=tile_mapping[map_style]
                )
                
                # Adicionar marcadores
                for idx, row in df.iterrows():
                    try:
                        lat = float(row[lat_col])
                        lon = float(row[lon_col])
                        
                        # Criar popup
                        if label_col != 'Nenhum':
                            popup_text = f"{row[label_col]}"
                        else:
                            popup_text = f"Ponto {idx + 1}"
                        
                        # Adicionar informações extras ao popup
                        popup_html = f"<b>{popup_text}</b><br>"
                        for col in df.columns:
                            if col not in [lat_col, lon_col]:
                                popup_html += f"{col}: {row[col]}<br>"
                        
                        folium.Marker(
                            location=[lat, lon],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=popup_text,
                            icon=folium.Icon(color='red' if marker_color == '#FF0000' else 'blue')
                        ).add_to(m)
                    except:
                        continue
                
                # Exibir o mapa
                st_folium(m, width=800, height=600)
            else:
                st.warning("⚠️ Por favor, verifique coordenadas (latitude e longitude).")
        
        # Chat com Gemini
        st.divider()
        st.subheader("💬 Chat com IA sobre seus Dados")
        
        if not api_key:
            st.warning("⚠️ Configure a API Key do Gemini.")
        else:
            # Exibir histórico do chat
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Input do usuário
            if prompt := st.chat_input("Pergunte algo sobre seus dados dos poços..."):
                # Adicionar mensagem do usuário
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Preparar contexto com os dados
                data_context = f"""
                Você é uma Analista de Dados chamada SETIMA-IA e está com os seguintes dados
                de instalação de poços:
                
                {df}

                Mostre o resultado da análise com base na solicitação do Gestor e nas Estatísticas iniciais:
                
                {len(df)}

                {df.describe().to_string()}

                Lembre-se que a localização dos poços está na coluna denominada {df['CIDADE']} e para somar 
                a quantidade deve-se contar o número de linhas em que aquela cidade aparece.

                """
                
                # Gerar resposta do Gemini
                try:
                    model = genai.GenerativeModel('gemini-2.5-pro')
                    full_prompt = f"{data_context}\n\nPergunta do Gestor: {prompt}"
                    response = model.generate_content(full_prompt)
                    
                    # Adicionar resposta da IA
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    with st.chat_message("assistant"):
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"Erro ao gerar resposta: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        #st.info("💡 Certifique-se de que o CSV contém colunas de latitude e longitude.")

else:
    # Tela inicial
    st.info("👆 Faça inclusão do dataset para começar!")
    
    st.markdown("""
    ### 📋Como usar:
    
    1. **🗺️Visualize** seu mapa interativo
    2. **📝Converse** com a IA sobre seus dados
       
    """)
# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Desenvolvido com ❤️ usando Streamlit, Folium e Gemini AI</p>
</div>
""", unsafe_allow_html=True)