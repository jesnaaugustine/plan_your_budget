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

# Custom CSS to style the page and sidebar
def apply_custom_css() -> None:
    """Applies custom CSS styling to the Streamlit page and sidebar."""
    st.markdown(
        """
        <style>
        /* Main background and text colors */
        body {
            background-color: #f0f8ff;  /* Light cyan background */
            color: #002B5B;  /* Dark blue text for readability */
        }
        .sidebar .sidebar-content {
            background-color: #006d77;  /* Dark cyan sidebar background */
            color: white;
            padding: 20px;
            border-right: 2px solid #003d5c;  /* Darker border */
        }
        .sidebar h2, .sidebar h4 {
            color: white;  /* White text for sidebar headings */
        }
        .block-container {
            background-color: white;  /* White content background */
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);  /* Subtle shadow for modern look */
        }
        /* Center content inside columns */
        .stColumn {
            text-align: center;
        }
        /* Style for the centered and bold footer text */
        .footer-text {
            font-size: 1.1rem;
            font-weight: bold;
            color: black;
            text-align: center;
            margin-top: 10px;
        }
        /* Style buttons to look modern and attractive */
        .stButton button {
            background-color: #118ab2;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
        }
        .stButton button:hover {
            background-color: #07a6c2;
            color: white;
        }
        /* Headings inside the main page */
        h1, h2, h3, h4 {
            color: #006d77;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Applied custom CSS styling.")


# Function to display logo or placeholder


# Function to display main content
def display_main_content() -> None:
    """Displays the main welcome content on the page."""
    st.title("Personal Document Assistant 📄🤖")
    st.markdown(
        """
        Welcome to the AI-Powered Document Retrieval Assistant 👋
                
        This app allows you to interact with an AI-powered assistant and upload documents for processing and retrieval.
        
        **Features:**
        - **Chatbot**: Have a conversation with the AI using the latest LLM model.
        - **Document Upload**: Upload PDFs and retrieve data from them using OpenSearch as a Hybrid RAG System.
        
        **Choose a page from the sidebar to begin!**
        """
    )
    logger.info("Displayed main welcome content.")


# Function to display sidebar content
def display_sidebar_content() -> None:
    """Displays headers and footer content in the sidebar."""
    st.sidebar.markdown(
        "<h2 style='text-align: center;'>Plan your budget with AI</h2>", unsafe_allow_html=True
    )
    st.sidebar.markdown(
        "<h4 style='text-align: center;'>Your Conversational Platform</h4>",
        unsafe_allow_html=True,
    )
   
    logger.info("Displayed sidebar content.")


# Main execution
if __name__ == "__main__":
    apply_custom_css()
    display_sidebar_content()
    display_main_content()

# uploaded_file = st.file_uploader(
#     "Upload bill or Excel",
#     type=["xlsx", "csv", "pdf",'png','jpg','jpeg']
# )

# if uploaded_file:
#     try:
#         st.success("File uploaded successfully")
#         file_path=raw_file_upload(uploaded_file.name,uploaded_file)
#         upload_time = datetime.now().strftime("%Y-%m-%d %H:%M%S")
#         insert_raw_data(conn,data=(uploaded_file.name,file_path,upload_time))
#         logger.info(f'raw file uploaded successfully. file path: {file_path}')

#         cleaned_data =process_file(file_path)

#         conn.close()
#     except Exception as e:
#         logger.exception(e)
#         st.error(f"Error processing file: {e}")
    



    
