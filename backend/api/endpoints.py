"""
endpoints.py

This module provides functions for handling chat interactions, adding PDF files, and populating PDF files from a
directory. It leverages clustering and embedding functionalities to enhance responses."""

import os
from cohere import Client

from algos.cluster import compute_cluster, give_closest_cluster
from db_funcs.file_storage import retrieve_pdfs, store_pdf, bulk_insert_pdf
from db_funcs.chat_history import retrieve_chat_history
from utils import extract_text

SAMPLE = [
    {'role': 'USER', 'text': 'What is autism?'},
    {'role': 'CHATBOT',
     'text': 'Autism is defined as a developmental disorder characterized by difficulties with social interaction and '
             'communication, and by restricted or repetitive patterns of thought and behavior. (Source: '
             'document-page1.pdf, Line 5)'},
    {'role': 'USER', 'text': 'What are the symptoms of autism?'},
    {'role': 'CHATBOT',
     'text': 'Symptoms of autism include challenges with social interactions, such as understanding and maintaining '
             'conversations, restricted interests, repetitive behaviors, and heightened sensitivity to sensory input. '
             '(Source: document-page2.pdf, Line 12)'}

]


def load_prompt(user_type: str) -> str:
    """
    Load and return a corresponding prompt from a text file based on the user type.

    Args:
        user_type (str): The type of user. Must be one of 'child', 'adult', or 'researcher'.

    Returns:
        str: The content of the corresponding prompt file.

    Raises:
        ValueError: If the user type is not one of 'child', 'adult', or 'researcher'.
        FileNotFoundError: If the corresponding prompt file does not exist.
    """
    valid_user_types = ['child', 'adult', 'researcher']

    if user_type not in valid_user_types:
        raise ValueError(f"Invalid user type. Expected one of {valid_user_types}, got '{user_type}'.")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'prompts', "rag", f"{user_type}.txt")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The prompt file for user type '{user_type}' does not exist at '{file_path}'.")

    with open(file_path, 'r', encoding='utf-8') as file:
        prompt = file.read()

    return prompt


def chat(prompt: str, username: str, usertype: str, co: Client) -> str:
    """
    Generate a chat response based on the given prompt and user's chat history.

    Args:
        prompt (str): The user's prompt to the chatbot.
        username (str): The username of the user interacting with the chatbot.
        co (Client): Cohere client for generating embeddings and chat responses.

    Returns:
        str: The chat response generated by the Cohere model.
    """
    closest_files = give_closest_cluster(prompt, co)
    files_content = retrieve_pdfs(closest_files)
    chat_history = retrieve_chat_history(username)
    texts = [extract_text(data) for data in files_content]
    documents = [{'title': closest_files[i], 'snippet': texts[i]} for i in range(len(closest_files))]
    prompt_format = load_prompt(usertype.lower()).format(username, prompt)
    print("Getting response")
    response = co.chat(
        model="command-r-plus",
        message=prompt_format,
        documents=documents,
        chat_history=chat_history
    )
    return response.text


def add_pdf(pdf_path: str, pdf_name: str, co: Client) -> None:
    """
    Add a PDF file to the database and update the cluster.

    Args:
        pdf_path (str): The path to the PDF file.
        pdf_name (str): The name to assign to the stored PDF file.
        co (Client): Cohere client for generating embeddings and updating clusters.
    """
    store_pdf(pdf_path, pdf_name)
    compute_cluster([pdf_name], co)


def populate_pdfs(directory_path: str, co: Client) -> None:
    """
    Add multiple PDF files from a directory to the database and update the cluster.

    Args:
        directory_path (str): The path to the directory containing PDF files.
        co (Client): Cohere client for generating embeddings and updating clusters.
    """
    files_list = [(filename, os.path.join(directory_path, filename)) for filename in os.listdir(directory_path)]
    bulk_insert_pdf(files_list)
    compute_cluster([file_pair[0] for file_pair in files_list], co)
