import os
import json
import re
import unicodedata
from langchain_community.document_loaders import (
    PyMuPDFLoader, 
    CSVLoader, 
    TextLoader, 
    Docx2txtLoader, 
    BSHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text, lowercase=False, remove_punctuation=False, remove_numbers=False):
    """
    Text normalization function with customizable parameters.
    - Removes extra whitespaces and newlines
    - Strips leading/trailing spaces
    - Optional: lowercase, remove_punctuation, remove_numbers
    """
    if not isinstance(text, str):
        return text
    
    if lowercase:
        text = text.lower()
        
    if remove_punctuation:
        text = re.sub(r'[^\w\s]', '', text)
        
    if remove_numbers:
        text = re.sub(r'\d+', '', text)
        
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def prepare_for_embedding(text):
    """
    Advanced text cleaning specifically designed to prepare text for vector embeddings.
    - Normalizes unicode characters
    - Removes zero-width spaces and control characters
    - Ensures clean spacing
    """
    if not isinstance(text, str):
        return text
        
    # 1. Normalize unicode characters (NFKC standardizes characters)
    text = unicodedata.normalize("NFKC", text)
    
    # 2. Remove control characters and zero-width spaces
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = text.replace('\u200b', '') # zero-width space
    
    # 3. Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def process_and_normalize_file(file_path, output_json_path="normalized_chunks.json", clean_metadata=True, clean_text_params=None):
    """
    Loads any supported document, chunks it intelligently, and normalizes the text.
    Supported formats: .pdf, .docx, .txt, .csv, .html, .md
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    print(f"Loading '{file_path}'...")
    file_name = file_path.lower()
    
    # 1. Select the right loader based on file extension
    try:
        if file_name.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        elif file_name.endswith(".csv"):
            loader = CSVLoader(file_path)
        elif file_name.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file_name.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif file_name.endswith(".html"):
            loader = BSHTMLLoader(file_path)
        elif file_name.endswith(".md"):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Supported types: docx, pdf, txt, html, md, csv.")
            
        documents = loader.load()
    except Exception as e:
        print(f"Failed to load document: {e}")
        return

    print("Chunking the document intelligently...")
    
    # 2. Use RecursiveCharacterTextSplitter to chunk without breaking sentences!
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Size of each chunk
        chunk_overlap=200,     # Overlap to preserve context between chunks
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Document split into {len(chunks)} chunks.")

    # 3. Normalize the chunks
    normalized_data = []
    if clean_text_params is None:
        clean_text_params = {}
        
    for i, chunk in enumerate(chunks):
        # Clean the text using provided parameters
        cleaned_text = clean_text(chunk.page_content, **clean_text_params)
        
        # Further prepare specifically for embeddings
        embedding_ready_text = prepare_for_embedding(cleaned_text)
        
        # Clean metadata to save space (remove creator, producer, dates, etc.)
        filtered_metadata = chunk.metadata
        if clean_metadata and isinstance(chunk.metadata, dict):
            # Keep only essential fields like source and page number
            filtered_metadata = {
                k: v for k, v in chunk.metadata.items() 
                if k in ["source", "page"]
            }
            
        # We store the cleaned text ready for embeddings, along with its metadata
        normalized_data.append({
            "chunk_id": i + 1,
            "source": file_path,
            "normalized_embedding_text": embedding_ready_text,
            "metadata": filtered_metadata
        })

    # 4. Save to JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, indent=4)
        
    print(f"Successfully processed and saved normalized text to '{output_json_path}'")
    
    # Print an example for the user
    if normalized_data:
        print("\n--- Example Normalized Output (Chunk 1) ---")
        print(f"Normalized Text:\n{normalized_data[0]['normalized_embedding_text'][:300]}...")
        print("-------------------------------------------\n")


    
INPUT_FILE = "AppBody-Sample-English.docx"
OUTPUT_FILE = "normalized_chunks.json"
    
# ⬇️ SET YOUR TEXT CLEANING PARAMETERS HERE ⬇️
CLEAN_PARAMS = {
    "lowercase": False,
    "remove_punctuation": True,
    "remove_numbers": True
}
    
process_and_normalize_file(
    file_path=INPUT_FILE, 
    output_json_path=OUTPUT_FILE, 
    clean_text_params=CLEAN_PARAMS
)
