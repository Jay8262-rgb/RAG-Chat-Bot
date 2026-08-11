from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data structure for queries
class QueryRequest(BaseModel):
    query: str

# 2. ADD THE QUERY ENDPOINT
@app.post("/api/query")
async def handle_query(request: QueryRequest):
    """
    This endpoint receives the chat query from the React frontend.
    You will connect this to your RAG system's retrieval logic.
    """
    user_question = request.query
    
    # ---------------------------------------------------------
    # RAG LOGIC INTEGRATION
    from functioning import function_process
    try:
        # Call the function with the user's query
        rag_response = function_process(user_question)
        
        # If the function returned a dictionary (like {"response": "..."}), extract it.
        # Otherwise, if it's the raw string or the API response, parse accordingly.
        if isinstance(rag_response, dict) and "response" in rag_response:
            bot_answer = rag_response["response"]
        else:
            bot_answer = str(rag_response)
            
    except Exception as e:
        bot_answer = f"Error processing query: {str(e)}"
    # ---------------------------------------------------------
    
    return {"response": bot_answer}

# 3. ADD THE FILE UPLOAD ENDPOINT
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    This endpoint receives the document uploaded from the React frontend.
    You will connect this to your document chunker/normalizer.
    """
    try:
        # Create a directory to store uploaded files temporarily if it doesn't exist
        upload_dir = "uploaded_docs"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = f"{upload_dir}/{file.filename}"
        
        # Save the file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # ---------------------------------------------------------
        # Process the document with normalized_chunks
        from normalized_chunks import process_and_normalize_file
        
        clean_params = {
            "lowercase": False,
            "remove_punctuation": True,
            "remove_numbers": True
        }
        
        process_and_normalize_file(
            file_path=file_path,
            output_json_path="normalized_chunks.json",
            clean_text_params=clean_params
        )
        # ---------------------------------------------------------
        from main import processing_file 
        processing_file("normalized_chunks.json")
        
        return {"message": f"Successfully uploaded and processed {file.filename}. ready file to next process"}
        
    except Exception as e:
        return {"message": f"There was an error uploading the file: {str(e)}"}

@app.get("/")
def read_root():
    return {"Hello": "RAG System Backend is Running!"}
