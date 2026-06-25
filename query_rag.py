import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Load these once, when the module is imported, not every time a question is asked
_embeddings = None
_db = None
_client = None

def _initialize():
    """Loads the FAISS index and Gemini client once, reusing them across calls."""
    global _embeddings, _db, _client
    if _db is not None:
        return  # already initialized, skip

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file!")

    _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    index_folder = "faiss_index" if os.path.exists("faiss_index") else "faiss_solar_index"
    if not os.path.exists(index_folder):
        raise FileNotFoundError(f"Index folder '{index_folder}' not found. Run build_rag.py first.")

    _db = FAISS.load_local(index_folder, _embeddings, allow_dangerous_deserialization=True)
    _client = genai.Client(api_key=api_key)

def ask_solar_advisor(user_query):
    """
    Takes a user question, retrieves relevant policy context, and returns
    a Gemini-generated answer. Returns a dict with the answer and whether
    it succeeded, so the caller can show errors honestly.
    """
    try:
        _initialize()

        matched_docs = _db.similarity_search(user_query, k=4) # type: ignore
        context_text = ""
        for i, doc in enumerate(matched_docs, 1):
            source_name = doc.metadata.get('source', 'Policy Doc')
            context_text += f"\n--- Context Snippet {i} (Source: {source_name}) ---\n{doc.page_content}\n"

        system_instruction = (
            "You are an expert AI Solar Energy Advisor for India. Your job is to answer questions "
            "accurately using ONLY the provided policy context from PM Surya Ghar Yojana, UPERC, or UPPCL.\n"
            "If you do not know the answer based on the context, say 'I cannot find that in the official documents.'\n"
            "Always maintain absolute accuracy regarding subsidy amounts, kW calculations, and financial rules."
        )

        compiled_prompt = f"Context available:\n{context_text}\n\nUser Question: {user_query}"

        response = _client.models.generate_content( # type: ignore 
            model='gemini-2.5-flash',
            contents=compiled_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        return {"success": True, "answer": response.text}

    except Exception as e:
        return {"success": False, "answer": f"Error: {e}"}


# This block only runs if you execute "python query_rag.py" directly,
# so your terminal testing still works exactly as before.
if __name__ == "__main__":
    print("Solar Policy Advisor Chatbot (type 'exit' to quit)")
    print("-" * 60)
    while True:
        user_query = input("\nAsk a question: ")
        if user_query.strip().lower() == 'exit':
            print("Goodbye!")
            break
        if not user_query.strip():
            continue
        result = ask_solar_advisor(user_query)
        print("\nAnswer:")
        print(result["answer"])