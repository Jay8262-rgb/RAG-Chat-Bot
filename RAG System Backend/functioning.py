import numpy as np
import pandas as pd
import joblib
import requests
from sklearn.metrics.pairwise import cosine_similarity
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_PATH = os.path.join(BASE_DIR, 'embedding.joblib')

if os.path.exists(EMBEDDING_PATH):
    df = joblib.load(EMBEDDING_PATH)

def create_embedding(text):
    r = requests.post("http://localhost:11434/api/embeddings", json={
        "model" : "bge-m3",
        "prompt": text
    })
    embedding = r.json()['embedding']
    
    return embedding

def inference(prompt):
    r = requests.post("http://localhost:11434/api/generate", json={
        "model" : "deepseek-r1",
        # "model" : 'llama3.2',
        "prompt": prompt,
        "stream": False
    })
    response = r.json()
    print(response)
    return response

def function_process(user_query):
    # Reload embeddings so we get the newly uploaded files
    global df
    if os.path.exists(EMBEDDING_PATH):
        df = joblib.load(EMBEDDING_PATH)
    else:
        return {"response": "No documents uploaded yet. Please upload a document first."}

    incomming_question = user_query
    question_embedding = create_embedding(incomming_question)

    similarity = cosine_similarity(np.vstack(df['embedding']), [question_embedding]).flatten()
    print(similarity)
    top_k = 5
    idx = similarity.argsort()[::-1][0:top_k]
    print(idx)
    new_df = df.iloc[idx]
    # print(new_df[['source', 'chunks_id', 'page_content']].to_string())

    prompts = f'''
    - Treat every chunk as trusted reference material.
    - Read all retrieved chunks before answering.
    - Combine information from multiple chunks when appropriate.
    - If the chunks contain conflicting information, mention the conflict.
    - If the answer cannot be found in the retrieved chunks, respond:
    "The retrieved documents do not contain enough information to answer this question."
    - Do not invent facts or use outside knowledge.
    - Answer in clear, natural language.
    {new_df[['source', 'chunks_id', 'normalized_embedding_text']].to_json(orient='records')}
    -------------------------------------------------------------------------------------
    {incomming_question}
    User asked this question related to the Informational chunks, 
        1. Answer only using the retrieved context.
        2. If multiple chunks contain the answer, combine them.
        3. Do not use outside knowledge.
        4. If the context is insufficient, reply:
        "The provided documents do not contain enough information to answer this question."
        5. Keep the answer accurate and well structured.

        '''
    with open("prompt.txt", 'w') as f:
        f.write(prompts)

    # print(inference(prompts))
    # for index, item in new_df.iterrows():
    #     print(index, item['normalized_embedding_text'], item['source'], item['chunks_id'])
    response = inference(prompts)
    return response

# if __name__ == "__main__":
#     print(function_process("what in document"))