import logging
import os
from src.utils import setup_logging
import streamlit as st

from src.utils import raw_file_upload,process_file

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Hey!!! Meet your AI budget analyzer!", page_icon="🤖"
)

uploaded_file = st.file_uploader(
    "Upload bill or Excel",
    type=["xlsx", "csv", "pdf",'png','jpg','jpeg']
)

if uploaded_file:
    st.success("File uploaded successfully")
    file_path =raw_file_upload(uploaded_file.name,uploaded_file)
    logger.info(f'raw file uploaded successfully. file path: {file_path}')

    process_file(file_path)


    
