import logging
from dotenv import load_dotenv
import os
from pathlib import Path
import uuid
import sqlite3
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

LOG_PATH = os.getenv("LOG_PATH")
def create_raw_data_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_file TEXT,
        unique_file TEXT,
        uploaded_date TEXT
    )
    """)

    conn.commit()
    return
def insert_raw_data(conn,data):
    insert_query = """
    INSERT INTO uploaded_files (
        raw_file,
        unique_file,
        uploaded_date
    )
    VALUES (?, ?, ?)
    """
    cursor =conn.cursor()
    cursor.execute(insert_query,data)
    conn.commit()
    


def setup_logging():
    ''' 
    setup logging setups for application.
    '''
    logging.basicConfig(filename =LOG_PATH,filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def raw_file_upload(file_name,file):
    #to avoid overwriting of same filename generate unique file name for each file
    unique_filename = f"{uuid.uuid4()}_{file_name}"
    save_path = os.path.join(BASE_DIR,
        "data/raw",
        unique_filename
    )

    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    
    return save_path

def process_file(file_path):
    pass
    