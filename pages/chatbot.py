import logging
import os
from dotenv import load_dotenv
from pathlib import Path


import streamlit as st
from src.opensearch import get_opensearch_client,create_index
from src.embeddings import get_embedding_model
from src.chats import ensure_model_pulled,generate_response_streaming,update_summary,get_recent_history

from src.utils import setup_logging
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")
OPENSEARCH_INDEX=os.getenv("OPENSEARCH_INDEX")
LATEST_CHAT_HISTORY = os.getenv("LATEST_CHAT_HISTORY")

# Initialize logger
setup_logging()  # Configures logging for the application
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(page_title="Plan your badget with AI - Chatbot", page_icon="🤖")

# Apply custom CSS
st.markdown(
    """
    <style>
    /* Main background and text colors */
    body { background-color: #f0f8ff; color: #002B5B; }
    .sidebar .sidebar-content { background-color: #006d77; color: white; padding: 20px; border-right: 2px solid #003d5c; }
    .sidebar h2, .sidebar h4 { color: white; }
    .block-container { background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); }
    .footer-text { font-size: 1.1rem; font-weight: bold; color: black; text-align: center; margin-top: 10px; }
    .stButton button { background-color: #118ab2; color: white; border-radius: 5px; padding: 10px 20px; font-size: 16px; }
    .stButton button:hover { background-color: #07a6c2; color: white; }
    h1, h2, h3, h4 { color: #006d77; }
    .stChatMessage { background-color: #e0f7fa; color: #006d77; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .stChatMessage.user { background-color: #118ab2; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)
logger.info("Custom CSS applied.")
def render_chatbot_page():
    # Set up a placeholder at the very top of the main content area
    st.title("Plan your budget with AI - Chatbot 🤖")
    model_loading_placeholder = st.empty()
    # Initialize session state variables for chatbot settings
    if "use_hybrid_search" not in st.session_state:
        st.session_state["use_hybrid_search"] = True
    if "num_results" not in st.session_state:
        st.session_state["num_results"] = 5
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.7

    with st.spinner("Connecting to OpenSearch..."):
        client = get_opensearch_client()
    index_name = OPENSEARCH_INDEX

    create_index(client)

    st.session_state["use_hybrid_search"] = st.sidebar.checkbox("Enable RAG mode", value=st.session_state["use_hybrid_search"])
    st.session_state["num_results"] = st.sidebar.number_input(
        "Number of Results in Context Window",
        min_value=1,
        max_value=10,
        value=st.session_state["num_results"],
        step=1,
    )
    st.session_state["temperature"] = st.sidebar.slider(
        "Response Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.1,
    )
    with model_loading_placeholder.container():
        st.spinner("Loading models for chat...")
    if "embedding_models_loaded" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading Embedding and Ollama models for Hybrid Search..."):
                get_embedding_model()
                ensure_model_pulled(OLLAMA_MODEL_NAME)
                st.session_state["embedding_models_loaded"] = True
        logger.info("Embedding model loaded.")
        model_loading_placeholder.empty()
    if "conversation_summary" not in st.session_state:
        st.session_state["conversation_summary"] = ""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        
    
    if prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        logger.info("User input received.")
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response_placeholder = st.empty()
                response_text = ""

                response_stream = generate_response_streaming(
                    prompt,
                    use_hybrid_search=st.session_state["use_hybrid_search"],
                    num_results=st.session_state["num_results"],
                    temperature=st.session_state["temperature"],
                    chat_history=st.session_state["chat_history"],
                    latest_chat_history_count =LATEST_CHAT_HISTORY,
                )
            if response_stream is not None:
                for chunk in response_stream:
                    logger.info(chunk)
                    logger.info(type(chunk))
                    logger.info(type(chunk.message))
                    content =chunk.message.content
                    if content:
                        response_text += content
                        response_placeholder.markdown(response_text + "▌")
                    else:
                        logger.error("Unexpected chunk format in response stream.")

            response_placeholder.markdown(response_text)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response_text}
            )
            logger.info("Response generated and displayed.")
            if len(st.session_state["chat_history"]) % 10 == 0:
                recent_history = get_recent_history(st.session_state["chat_history"],no_recent_chat=10)

                st.session_state['conversation_summary'] =update_summary(recent_history,st.session_state['conversation_summary'])


            

if __name__ == "__main__":
    render_chatbot_page()