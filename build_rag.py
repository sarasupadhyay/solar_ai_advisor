import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import glob

# Load environment variables (your Gemini API key)
load_dotenv()

# Step 1: Find all PDF files across your three folders
folders = [
    "Solar_documents/Central_Schemes",
    "Solar_documents/State_rules",
    "Solar_documents/Tariff_orders"
]

all_pdf_paths = []
for folder in folders:
    pdfs = glob.glob(f"{folder}/*.pdf")
    all_pdf_paths.extend(pdfs)

print(f"Found {len(all_pdf_paths)} PDF files total.")

# Step 2: Load every PDF into memory as documents
all_documents = []
for path in all_pdf_paths:
    try:
        loader = PyPDFLoader(path)
        docs = loader.load()
        all_documents.extend(docs)
        print(f"Loaded: {path} ({len(docs)} pages)")
    except Exception as e:
        print(f"FAILED to load {path}: {e}")

print(f"\nTotal pages loaded across all documents: {len(all_documents)}")

# Step 3: Split documents into smaller chunks for better retrieval
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
chunks = text_splitter.split_documents(all_documents)
print(f"Split into {len(chunks)} chunks.")

# Step 4: Create embeddings (converts text into number-vectors)
print("\nCreating embeddings... this may take a few minutes the first time.")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Step 5: Build the FAISS index and save it to disk
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("faiss_index")

print("\nDone! Your FAISS index has been saved to the 'faiss_index' folder.")