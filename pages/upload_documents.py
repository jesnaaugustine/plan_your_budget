import logging
import os
import time
from datetime import datetime
from dateutil.parser import parse
import uuid

import streamlit as st
from PyPDF2 import PdfReader
from src.embeddings import get_embedding_model,generate_embeddings
from src.opensearch import get_opensearch_client,create_index,bulk_index_documents
from src.utils import setup_logging,raw_file_upload,chunk_text
from src.file_processor import process_file
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent


# Initialize logger
setup_logging()  # Set up centralized logging configuration
logger = logging.getLogger(__name__)
load_dotenv(BASE_DIR / ".env")

OPENSEARCH_INDEX=os.getenv("OPENSEARCH_INDEX")
TEXT_CHUNK_SIZE=os.getenv("TEXT_CHUNK_SIZE")
OVERLAP_SIZE=os.getenv("OVERLAP_SIZE")

# Set page config with title, icon, and layout
st.set_page_config(page_title="Plan your budget with AI - Upload Documents", page_icon="📂")
# Set page config with title, icon, and layout
st.set_page_config(page_title="Plan your budget with AI - Upload Documents", page_icon="📂")
# Custom CSS to style the page and sidebar
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
    .stButton.delete-button button { background-color: #e63946; color: white; font-size: 14px; }
    .stButton.delete-button button:hover { background-color: #ff4c4c; }
    h1, h2, h3, h4 { color: #006d77; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Sidebar header
st.sidebar.markdown(
    "<h2 style='text-align: center;'Plan Budget with AI</h2>", unsafe_allow_html=True
)
st.sidebar.markdown(
    "<h4 style='text-align: center;'>Your Document Assistant</h4>",
    unsafe_allow_html=True,
)

def render_upload_page() -> None:
    st.title("Upload Documents")
    # Placeholder for the loading spinner at the top
    model_loading_placeholder = st.empty()

    # Display the loading spinner at the top for loading the embedding model
    if "embedding_models_loaded" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading models for document processing..."):
                get_embedding_model()
                st.session_state["embedding_models_loaded"] = True
        logger.info("Embedding models loaded.")
        model_loading_placeholder.empty()  # Clear the placeholder after loading
    UPLOAD_DIR = BASE_DIR / "data"/'raw'
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with st.spinner("Connecting to OpenSearch..."):
        client = get_opensearch_client()
    index_name = OPENSEARCH_INDEX
    create_index(client)

    tab1, tab2 = st.tabs(["Upload Bill","Manual Entry"])
    with tab1:
        uploaded_files = st.file_uploader(
        "Upload PDF documents", type=[ "pdf",'png','jpg','jpeg'], accept_multiple_files=True)
        if uploaded_files:
            with st.spinner("Uploading and processing documents. Please wait..."):
                for uploaded_file in uploaded_files:
                    file_path=raw_file_upload(uploaded_file.name,uploaded_file,file_type ='document')
                    #upload_time = datetime.now().strftime("%Y-%m-%d %H:%M%S")
                    #insert_raw_data(conn,data=(uploaded_file.name,file_path,upload_time))
                    logger.info(f'raw file uploaded successfully. file path: {file_path}')

                    cleaned_data =process_file(file_path)
                    logger.info(cleaned_data)
                    chunks = chunk_text(cleaned_data,chunk_size =TEXT_CHUNK_SIZE,overlap_size=OVERLAP_SIZE)
                    logger.info(chunks)
                    embeddings = generate_embeddings(chunks)
                    normalized_date = [parse(date_str, dayfirst=True).strftime("%Y-%m-%d") for date_str in cleaned_data["dates"]]

                    documents_to_index = [
                        {
                            "doc_id": f"{uploaded_file.name}_{i}",
                            "text": chunk,
                            "embedding": embedding,
                            "dates": normalized_date,
                            "business_keywords":cleaned_data['bussiness_keywords'],
                            "document_name": uploaded_file.name,

                        }
                        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                    ]
                    bulk_index_documents(documents_to_index)
                    st.session_state["documents"].append(
                        {
                            "filename": uploaded_file.name,
                            "content": cleaned_data['text'],
                            "file_path": file_path,
                        }
                    )
                    logger.info(f"File '{uploaded_file.name}' uploaded and indexed.")
    with tab2:
        if st.session_state.get("clear_text", False):
            st.session_state["manual_expense"] = ""
            st.session_state["clear_text"] = False

        expense_text = st.text_area( "Enter expense details", key="manual_expense")
        if st.button("Save Expense"):
            with st.spinner("Processing text. Please wait..."):
                file_path=raw_file_upload('manual_entry_text.txt',expense_text,file_type ='manual')
                #upload_time = datetime.now().strftime("%Y-%m-%d %H:%M%S")
                #insert_raw_data(conn,data=(uploaded_file.name,file_path,upload_time))
                logger.info(f'raw file uploaded successfully. file path: {file_path}')

                cleaned_data =process_file(file_path)
                logger.info(cleaned_data)
                chunks = chunk_text(cleaned_data,chunk_size =TEXT_CHUNK_SIZE,overlap_size=OVERLAP_SIZE)
                logger.info(chunks)
                embeddings = generate_embeddings(chunks)
                normalized_date = [parse(date_str, dayfirst=True).strftime("%Y-%m-%d") for date_str in cleaned_data["dates"]]
                unique_filename = f"{uuid.uuid4()}_text.txt"
                documents_to_index = [
                    {
                        "doc_id": f"{unique_filename}_{i}",
                        "text": chunk,
                        "embedding": embedding,
                        "dates": normalized_date,
                        "business_keywords":cleaned_data['bussiness_keywords'],
                        "document_name": unique_filename,

                    }
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                bulk_index_documents(documents_to_index)
                st.session_state["documents"].append(
                    {
                        "filename": unique_filename,
                        "content": cleaned_data['text'],
                        "file_path": file_path,
                    }
                )
                #st.session_state.manual_expense=''
                #text_entering_placeholder.empty()
            st.session_state["clear_text"] = True
            st.rerun()
            logger.info(f"File {unique_filename} uploaded and indexed.")


if __name__ == "__main__":
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    render_upload_page()