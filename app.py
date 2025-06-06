import json
import os
import uuid
import streamlit as st
import requests

# Configurações
st.set_page_config(page_title="Chat com API", layout="wide")
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# URL da API (ajuste se necessário)

# Para produção
API_URL = "https://web-production-6daa.up.railway.app"

# Para testes
#API_URL = "http://localhost:8000"


# Estado inicial
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ TELA DE LOGIN ------------------
if not st.session_state.access_token:
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            try:
                response = requests.post(f"{API_URL}/auth/login", data={
                    "username": username,
                    "password": password
                })

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.username = username
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha inválidos.")
            except Exception as e:
                st.error(f"Erro na conexão: {e}")
    st.stop()

# ------------------ APP PRINCIPAL (após login) ------------------

page = st.sidebar.radio("📄 Navegação", ["💬 Chatbot", "📖 Como Usar"])

if page == "📖 Como Usar":
    st.title("📖 Como Usar o Chatbot")
    st.markdown(f"Você está logado como: **{st.session_state.username}**")
    st.markdown("🔒 Token ativo: `Bearer ...`")

    st.header("🧭 Instruções")
    st.markdown("""
    Este chatbot conecta-se a uma API protegida por autenticação. Aqui está como utilizá-lo:

    1. **Faça o login** com suas credenciais válidas.
    2. **Após o login**, vá para a aba **💬 Chatbot**.
    3. **Digite sua mensagem** no campo de entrada ao final da página.
    4. **As mensagens serão armazenadas** localmente e também podem ser salvas via botão de exportação.
    5. **Use a opção "Encerrar Sessão"** para sair com segurança.

    #### Funcionalidades extras:
    - **💾 Baixar histórico (.csv)**: Exporta todas as conversas.
    - **🛑 Encerrar Sessão**: Encerra a conexão com a API.
    """)
else:
    st.title("🤖 Chatbot via API")

    # Sidebar
    #st.sidebar.header("🔧 Configurações")
    #openai_key = st.sidebar.text_input("🔑 Chave do GPT", type="password")

    # Botões extras
    if st.sidebar.button("💾 Salvar Histórico (.csv)"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            response = requests.get(f"{API_URL}/history", headers=headers)

            if response.status_code == 200:
                st.sidebar.download_button(
                    label="📥 Clique aqui para baixar o CSV",
                    data=response.content,
                    file_name="historico.csv",
                    mime="text/csv"
                )
            else:
                st.sidebar.warning("Erro ao baixar histórico.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

    if st.sidebar.button("🛑 Sair da sessão"):
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        requests.post(f"{API_URL}/end_conection", headers=headers)
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()
    # Mostrar conversa
    for msg in st.session_state.messages:
        col1, col2 = st.columns([1, 5]) if msg["role"] == "user" else st.columns([5, 1])
        with (col2 if msg["role"] == "user" else col1):
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

    # Campo de entrada (movido para o final)
    user_input = st.chat_input("Digite sua mensagem...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        json_data = {
            #"openai_key": openai_key,
            "content": user_input
        }
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

        try:
            response = requests.post(API_URL + "/", json=json_data, headers=headers)
            if response.status_code == 200:
                bot_reply = response.json()[-1]["content"]
            else:
                bot_reply = f"⚠️ Erro {response.status_code}: {response.text}"
        except Exception as e:
            bot_reply = f"❌ Erro: {e}"

        st.session_state.messages.append({"role": "bot", "content": bot_reply})
        st.rerun()
