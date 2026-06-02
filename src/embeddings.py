import logging
from typing import Any, List
from pathlib import Path
import numpy as np
import streamlit as st
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from src.utils import setup_logging

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL_PATH =os.getenv("EMBEDDING_MODEL_PATH")

# Initialize logger
setup_logging()  # Configures logging for the application
logger = logging.getLogger(__name__)

@st.cache_resource(show_spinner=False)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads and caches the embedding model.

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    logger.info(f"Loading embedding model from path: {EMBEDDING_MODEL_PATH}")
    return SentenceTransformer(EMBEDDING_MODEL_PATH)

def generate_embeddings(chunks):
    model =get_embedding_model()
    embeddings = [np.array(model.encode(chunk)) for chunk in chunks]
    logger.info(f"Generated embeddings for {len(chunks)} text chunks.")
    return embeddings

