import os
import json
import chromadb
from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer

# Load model for embeddings (same as indexer)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@tool
def search_courses(query: str, n_results: int = 5) -> str:
    """
    Searches for courses in ChromaDB based on a semantic query (e.g., 'python for beginners').
    Use this to find courses that fill the identified user gaps.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    chroma_db_dir = os.path.join(base_dir, "chroma_db")
    
    try:
        client = chromadb.PersistentClient(path=chroma_db_dir)
        collection = client.get_collection(name="courses_collection")
        
        # Calculate embedding for the query
        query_vector = embedding_model.encode([query]).tolist()
        
        results = collection.query(
            query_embeddings=query_vector,
            n_results=n_results
        )
        
        return json.dumps(results['metadatas'], indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error searching courses: {str(e)}"
