import os
#from dotenv import load_dotenv
import streamlit as st
from io import StringIO
import google.generativeai as ggi

#load_dotenv()
#load_dotenv(".env")

fetcheed_api_key = os.getenv("GOOGLE_API_KEY")
ggi.configure(api_key = fetcheed_api_key)

#model = ggi.GenerativeModel("gemini-1.5-pro") 
model = ggi.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat()

def LLM_Response(question):
    response = chat.send_message(question, stream=True)
    return response

# Configuração básica da página
st.set_page_config(page_title="Chat com Gemini", layout="centered")

# Título estilizado
st.title("Chat Aplicação usando Gemini key!")

# Estilização básica com CSS
st.markdown("""
<style>
.stTextInput input {
  border-radius: 8px;
  border: 1px solid #ccc;
  padding: 8px;
}
h1 {
  font-family: 'Segoe UI', sans-serif;
  font-size: 2.2rem;
  color: #333333;
  letter-spacing: 1px;
  margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Explicação rápida
st.write("Faça uma pergunta e receba uma resposta da IA!")

# Campo de entrada
with st.container():
    user_quest = st.text_input("Digite sua pergunta aqui:", placeholder="Ex: Qual a capital da Noruega?")

    # Botão centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn = st.button("Resposta")

# Exibir a resposta
if btn and user_quest:
    with st.spinner("Pensando..."):
        result = LLM_Response(user_quest)
        st.markdown("### 💬 Resposta:")
        for word in result:
            st.write(word.text)

# Fontes
# https://medium.com/@speaktoharisudhan/building-a-gemini-powered-chatbot-in-streamlit-e241ed5958c4
# https://medium.com/@suraj_bansal/build-your-own-ai-chatbot-a-beginners-guide-to-rag-and-langchain-0189a18ec401
# https://blog.jetbrains.com/pt-br/pycharm/2025/05/como-criar-chatbots-com-o-langchain/#
# https://www.youtube.com/watch?v=tsh0oSAdoBk
# https://towardsdatascience.com/step-by-step-guide-to-build-and-deploy-an-llm-powered-chat-with-memory-in-streamlit/
# https://ai.google.dev/edge/mediapipe/solutions/genai/function_calling/android?hl=pt-br

# fonte Antonio Carlos:
# https://www.youtube.com/watch?v=jbJpAdGlKVY - Aprendendo a usar css no streamlit
# https://www.youtube.com/watch?v=jUNCsyRTQMs&pp=ygUUZXN0cnV0dXJhIHN0cmVhbWlsaXQ%3D - estrutura basica
