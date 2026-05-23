import logging
from dotenv import load_dotenv
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

LOG_PATH = os.getenv("LOG_PATH")





def setup_logging():
    ''' 
    setup logging setups for application.
    '''
    logging.basicConfig(filename =LOG_PATH,filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def raw_file_upload(file_name,file):
    save_path = os.path.join(BASE_DIR,
        "data/raw",
        file_name
    )

    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    
    return save_path

def process_file(file_path):
    pass