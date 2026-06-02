
import ollama
import streamlit as st
import logging
from pathlib import Path
from dotenv import load_dotenv
import os


from src.embeddings import get_embedding_model

from src.utils import setup_logging
from src.opensearch import hybrid_search

# Initialize logger
setup_logging()
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

OLLAMA_MODEL_NAME =os.getenv("OLLAMA_MODEL_NAME")
ASSYMETRIC_EMBEDDING=os.getenv("ASSYMETRIC_EMBEDDING")

@st.cache_resource(show_spinner=False)
def ensure_model_pulled(model):
    try:
        available_models = ollama.list()
        if model not in available_models:
            logger.info(f"Model {model} not found locally. Pulling the model...")
            ollama.pull(model)
            logger.info(f"Model {model} has been pulled and is now available locally.")
        else:
            logger.info(f"Model {model} is already available locally.")
    except ollama.ResponseError as e:
        logger.error(f"Error checking or pulling model: {e.error}")
        return False
    return True
def generate_response_streaming(query,use_hybrid_search,num_results,temperature,latest_chat_history_count=5,chat_history=None):
    chat_history = chat_history or []
    max_history_messages = 10
    history = chat_history[-max_history_messages:]
    context = ""

    if use_hybrid_search:
        logger.info("Performing hybrid search.")
        if ASSYMETRIC_EMBEDDING:
            prefixed_query = f"passage: {query}"
        else:
            prefixed_query = f"{query}"
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.encode( prefixed_query).tolist() 
        search_results = hybrid_search(query, query_embedding, top_k=num_results)
        
        for i, result in enumerate(search_results):
            context += f"Document {i}:\n{result['_source']['text']}\n\n"
        logger.info(f"search completer:{context}")

        prompt = prompt_template(query, context, history,latest_chat_history_count)
        return run_llama_streaming(prompt, temperature)


def prompt_template(query,context,history,latest_chat_history_count):
    if len(history)>len(latest_chat_history_count):
        latest_history = history[-int(latest_chat_history_count):]
    else:
        latest_history = history

    history_text = "\n".join([
    f"{msg['role'].upper()}: {msg['content']}"
    for msg in latest_history
    ])
    if not context:
        context ="Answer questions to the best of your knowledge."


    prompt = f"""
    You are a personal financial assistant.

    Instructions:
    - Answer only using the provided financial records.
    - If information is missing, say "I could not find that information in your documents."
    - Use calculations when necessary.
    - Be concise and accurate.
    - Never make up expenses.

    Previous Conversation:
    {history_text}

    Financial Records:
    {context}

    Current Question:
    {query}

    Answer:
    """
    logger.info("Prompt constructed with context and conversation history.")
    return prompt

def run_llama_streaming(prompt,temperature):
    try:
        # Now attempt to stream the response from the model
        logger.info("Streaming response from LLaMA model.")
        logger.info(f'model:{OLLAMA_MODEL_NAME}')
        stream = ollama.chat(
            model=OLLAMA_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"temperature": temperature},
        )
        logger.info(stream)
    except ollama.ResponseError as e:
        logger.error(f"Error during streaming: {e.error}")
        return None

    return stream

def build_summary_prompt(
    existing_summary,
    recent_messages
    ):
        return f"""
    You are maintaining a memory summary for a personal finance assistant.

    Current Summary:
    {existing_summary}

    New Conversation:
    {recent_messages}

    Update the summary.

    Rules:
    - Keep important financial facts.
    - Keep conclusions already discussed.
    - Keep user preferences.
    - Remove unnecessary details.
    - Maximum 200 words.

    Updated Summary:
    """

def get_recent_history(chat_history, no_recent_chat=10):
    return "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in chat_history[-no_recent_chat:]
    )

def update_summary(recent_history, current_summary):
    summary_prompt = build_summary_prompt(
    current_summary,
    recent_history
    )

    response = ollama.chat(
        model=OLLAMA_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": summary_prompt
            }
        ]
    )

    new_summary = response.message.content

    return new_summary


