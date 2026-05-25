import logging
import os
from src.utils import setup_logging
import streamlit as st
from datetime import datetime

from src.utils import raw_file_upload,create_raw_data_table,insert_raw_data
from src.file_processor import process_file
import sqlite3
conn = sqlite3.connect("database/finance.db")
create_raw_data_table(conn)


setup_logging()
logger = logging.getLogger(__name__)
logger.info('connected to DB sucessfully!')

st.set_page_config(
    page_title="Hey!!! Meet your AI budget analyzer!", page_icon="🤖"
)

uploaded_file = st.file_uploader(
    "Upload bill or Excel",
    type=["xlsx", "csv", "pdf",'png','jpg','jpeg']
)

if uploaded_file:
    try:
        st.success("File uploaded successfully")
        file_path=raw_file_upload(uploaded_file.name,uploaded_file)
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M%S")
        insert_raw_data(conn,data=(uploaded_file.name,file_path,upload_time))
        logger.info(f'raw file uploaded successfully. file path: {file_path}')

        process_file(file_path)
        conn.close()
    except Exception as e:
        logger.exception(e)
        st.error(f"Error processing file: {e}")
    



    
