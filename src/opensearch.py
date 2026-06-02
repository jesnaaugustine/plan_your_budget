import logging
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from src.utils import setup_logging

# Initialize logger
setup_logging()
logger = logging.getLogger(__name__)

from opensearchpy import OpenSearch,helpers

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST")
OPENSEARCH_PORT =os.getenv("OPENSEARCH_PORT")
OPENSEARCH_INDEX=os.getenv("OPENSEARCH_INDEX")
EMBEDDING_DIMENSION=os.getenv("EMBEDDING_DIMENSION")
ASSYMETRIC_EMBEDDING=os.getenv("ASSYMETRIC_EMBEDDING")

def get_opensearch_client() -> OpenSearch:
    """
    Initializes and returns an OpenSearch client.

    Returns:
        OpenSearch: Configured OpenSearch client instance.
    """
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_compress=True,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    logger.info("OpenSearch client initialized.")
    return client

def load_index_config() -> Dict[str, Any]:
    """
    Loads the index configuration from a JSON file.

    Returns:
        Dict[str, Any]: The index configuration as a dictionary.
    """
    with open("src/index_config.json", "r") as f:
        config = json.load(f)

    # Replace the placeholder with the actual embedding dimension
    config["mappings"]["properties"]["embedding"]["dimension"] = EMBEDDING_DIMENSION
    logger.info("Index configuration loaded from src/index_config.json.")
    return config if isinstance(config, dict) else {}


def create_index(client: OpenSearch) -> None:
    """
    Creates an index in OpenSearch using settings and mappings from the configuration file.

    Args:
        client (OpenSearch): OpenSearch client instance.
    """
    index_body = load_index_config()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        response = client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        logger.info(f"Created index {OPENSEARCH_INDEX}: {response}")
    else:
        logger.info(f"Index {OPENSEARCH_INDEX} already exists.")


def bulk_index_documents(documents):
    actions = []
    client = get_opensearch_client()
    for doc in documents:
        doc_id = doc["doc_id"]
        embedding_list = doc["embedding"].tolist()
        document_name = doc["document_name"]
        dates=doc['dates']
        business_keywords=doc['business_keywords']


        # Prefix each document's text with "passage: " for the asymmetric embedding model
        if ASSYMETRIC_EMBEDDING:
            prefixed_text = f"passage: {doc['text']}"
        else:
            prefixed_text = f"{doc['text']}"

        action = {
            "_index": OPENSEARCH_INDEX,
            "_id": doc_id,
            "_source": {
                "text": prefixed_text,
                "embedding": embedding_list,  # Precomputed embedding
                "dates":dates,
                "business_keywords":business_keywords,
                "document_name": document_name,
            },
        }
        actions.append(action)

    # Perform bulk indexing and capture response details explicitly
    success, errors = helpers.bulk(client, actions)
    logger.info(
        f"Bulk indexed {len(documents)} documents into index {OPENSEARCH_INDEX} with {len(errors)} errors."
    )
    return success, errors


def hybrid_search(query_text,query_embedding, top_k):
    
    client = get_opensearch_client()
    #we can add metadata filter along with this query for improvement
    query_body = {
        "_source": {"exclude": ["embedding"]},  # Exclude embeddings from the results
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"text": {"query": query_text}}},  # Text-based search
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": top_k,
                            }
                        }
                    },
                ]
            }
        },
        "size": top_k,
    }

    response = client.search(
        index=OPENSEARCH_INDEX, body=query_body
    )
    logger.info(f"Hybrid search completed for query '{query_text}' with top_k={top_k}.")

    # Type casting for compatibility with expected return type
    hits: List[Dict[str, Any]] = response["hits"]["hits"]
    return hits