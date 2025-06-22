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
    response = chat.send_message(question,stream=True)
    return response

st.title("Chat Application using Gemini KEY")

st.markdown("""
<style>
.stTextInput input {
  border-radius: 8px;
  border: 1px solid #ccc;
  padding: 8px;
}
</style>
""", unsafe_allow_html=True)

user_quest = st.text_input("faça sua pergunta:")
btn = st.button("Resposta")

if btn and user_quest:
    result = LLM_Response(user_quest)
    st.subheader("Response : ")
    for word in result:
        st.text(word.text)

#fonte:
#https://medium.com/@speaktoharisudhan/building-a-gemini-powered-chatbot-in-streamlit-e241ed5958c4
#https://medium.com/@suraj_bansal/build-your-own-ai-chatbot-a-beginners-guide-to-rag-and-langchain-0189a18ec401
#https://blog.jetbrains.com/pt-br/pycharm/2025/05/como-criar-chatbots-com-o-langchain/#
#https://blog.jetbrains.com/pt-br/pycharm/2025/05/como-criar-chatbots-com-o-langchain/#

#https://www.youtube.com/watch?v=tsh0oSAdoBk
#https://towardsdatascience.com/step-by-step-guide-to-build-and-deploy-an-llm-powered-chat-with-memory-in-streamlit/
#https://ai.google.dev/edge/mediapipe/solutions/genai/function_calling/android?hl=pt-br
