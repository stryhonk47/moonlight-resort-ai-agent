import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
CHROMA_DB_DIR = os.path.join(BASE_DIR, os.getenv("CHROMA_DB_DIR", "chroma_db"))

def load_and_process_pdfs():
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"❌ No se encontraron archivos PDF en: {PDF_DIR}")
    
    documents = []
    for file_path in pdf_files:
        loader = PyPDFLoader(file_path)
        documents.extend(loader.load())
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_documents(documents)

def create_vector_store():
    chunks = load_and_process_pdfs()
    
    print("🧠 Cargando modelo de Embeddings Local (HuggingFace)...")
    # Genera embeddings en tu máquina sin necesidad de API Key ni cuotas
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print(f"💾 Guardando base de datos vectorial en: {CHROMA_DB_DIR}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    print("✅ ¡Indexación local completada sin límites de API!")
    return vector_store

if __name__ == "__main__":
    create_vector_store()