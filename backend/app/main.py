import os
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import google.generativeai as genai
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the .env file")

# Configure Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamically get the `docs` folder path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_FOLDER = os.path.join(BASE_DIR, "docs")

# Ensure the folder exists
if not os.path.exists(DOCS_FOLDER):
    os.makedirs(DOCS_FOLDER)

print("Docs folder path:", DOCS_FOLDER)

# Supported file types
SUPPORTED_FORMATS = {".pdf", ".txt", ".docx", ".xlsx"}


class QueryRequest(BaseModel):
    query: str


def load_all_files():
    """Loads all supported files from the `docs` folder and returns chunked text."""
    chunk_store = []
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    print(f"Checking files in: {DOCS_FOLDER}")
    files_found = os.listdir(DOCS_FOLDER)
    print(f"Files found: {files_found}")

    if not files_found:
        print("No files found in the docs folder.")

    for filename in files_found:
        file_path = os.path.join(DOCS_FOLDER, filename)
        ext = os.path.splitext(filename)[-1].lower()

        print(f"Processing file: {file_path} (Extension: {ext})")

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext == ".txt":
                loader = TextLoader(file_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(file_path)
            else:
                print(f"Skipping unsupported file: {filename}")
                continue  # Skip unsupported formats

            documents = loader.load()
            chunks = text_splitter.split_documents(documents)
            chunk_store.extend([chunk.page_content for chunk in chunks])

            print(f"Loaded {filename} with {len(chunks)} chunks")
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    return chunk_store


@app.post("/query/")
async def query_gemini(request: QueryRequest):
    """Loads all files, processes them, and returns AI-generated response."""
    try:
        chunk_store = load_all_files()

        if not chunk_store:
            raise HTTPException(
                status_code=400, detail="No valid files found in docs folder."
            )

        # Prepare the context from loaded file data
        prompt = f"Context: {' '.join(chunk_store)}\n\nUser Query: {request.query}"

        # Initialize Gemini Pro Model
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        return {
            "query": request.query,
            "response": response.text,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
