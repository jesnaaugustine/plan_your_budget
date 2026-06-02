import logging
from dotenv import load_dotenv
import os
from pathlib import Path
import uuid
import sqlite3
import re
import dateparser
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

def raw_file_upload(file_name,file,file_type ='document'):
    #to avoid overwriting of same filename generate unique file name for each file
    
    if file_type=='document':
        unique_filename = f"{uuid.uuid4()}_{file_name}"
        save_path = os.path.join(BASE_DIR,
        "data/raw",
        unique_filename
             )
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
    else:
        unique_filename = file_name
        save_path = os.path.join(BASE_DIR,
        "data/raw",
        unique_filename
             )
        with open(save_path, "a",encoding="utf-8") as f:
            f.write(file)
            f.write('\n---end_of_text---\n')

        
    return save_path

def clean_text(text):
    # Remove hyphens at line breaks (e.g., 'exam-\nple' -> 'example')
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Replace newlines within sentences with spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"₹\s*","₹",text)
    text = re.sub(r"₹", " ₹", text)

    cleaned_text = text.strip()
    
    dates =extract_dates(cleaned_text)
    bussiness_keywords =extract_bussiness(cleaned_text)
    data ={'dates':dates,'bussiness_keywords':bussiness_keywords,'text':cleaned_text}
    return data

def extract_dates(text):


    patterns = r'''
\b(
    \d{4}[-/]\d{2}[-/]\d{2} |   # YYYY-MM-DD or YYYY/MM/DD
    \d{2}[-/]\d{2}[-/]\d{4} |   # DD-MM-YYYY or DD/MM/YYYY
    \d{2}[-/]\d{2}[-/]\d{2}  |
    \d{4}[-/]\d{2}[-/]\d{2}
    (?:\s+\d{2}:\d{2})?   # DD-MM-YY or YY-MM-DD etc.
)\b
'''

    extracted_dates = []

    matches = re.findall(patterns, text,re.VERBOSE)

    # for match in matches:

    #     parsed_date = dateparser.parse(match)

    #     if parsed_date:

    #         extracted_dates.append(parsed_date)

    return matches
def extract_bussiness(text):
    business_keywords = [
    "restaurant",
    "hotel",
    "mart",
    "store",
    "tiffins",
    "cafe",
    "electronics",
    "fashion",
    "amazon",
    "electronics",
    "flipkart",
    "Dmart"
]
    lines =text.split('\n')
    top_lines =lines[:10] #assuming bussines may appear in first 10 lines of bill
    possible_vendors = []

    for line in top_lines:

        line_lower = line.lower()
        for keyword in business_keywords:
            if keyword.lower() in line_lower:
                possible_vendors.append(keyword)
    return possible_vendors

def chunk_text(data,chunk_size,overlap_size):
    splitter = RecursiveCharacterTextSplitter(
    chunk_size=int(chunk_size),
    chunk_overlap=int(overlap_size)
        )

    chunks = splitter.split_text(data['text'])
    enhanced_chunks = []
    for chunk in chunks:
        enriched_chunk = f"""
        Vendor: {data['bussiness_keywords']}
        Invoice Date: {data['dates']}
        {chunk}
        """

        enhanced_chunks.append(enriched_chunk)
    return enhanced_chunks


