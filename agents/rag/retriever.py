import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Base Paths Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# 2. Local Environment Setup
# We use the same embedding model as the indexer to ensure vector compatibility
print("[INFO] Loading retrieval environment...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Access the indexed collection
collection = client.get_or_create_collection(name="courses_collection")

def retrieve_relevant_courses(competency_profile: dict, top_k: int = 5, gaps: list = None) -> list:
    """
    Analyzes the competency profile and prioritized gaps to search for the most relevant
    courses in the vector database.
    """
    
    # A) Build the search query
    # Priority 1: Use the gaps calculated by the Gap Analyzer node (if available)
    if gaps:
        gap_names = [g.get("name", "") if isinstance(g, dict) else str(g) for g in gaps]
        search_query = f"Courses focusing on these specific competency gaps: {', '.join(gap_names)}"
        print(f"[INFO] Using Prioritized Gaps for RAG: {gap_names}")
    else:
        # Priority 2: Fallback to basic profile analysis
        internal_gaps = []
        competencies = competency_profile.get("competencies", [])
        for comp in competencies:
            if comp.get("level") == "bajo" or comp.get("score", 1.0) < 0.5:
                internal_gaps.append(comp.get("name", ""))
        
        if not internal_gaps:
            search_query = "general professional development and soft skills"
        else:
            search_query = f"Courses focusing on: {', '.join(internal_gaps)}"
        print(f"[INFO] Using Fallback Profile Analysis for RAG.")
    
    print(f"[INFO] Semantic Query: '{search_query}'")

    # B) Convert query to vector
    query_vector = embedding_model.encode([search_query]).tolist()

    # C) Query ChromaDB
    # We retrieve metadata to pass it to the Planning Agent (Agent 2)
    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k
    )

    # D) Format the output for the LangGraph State
    retrieved_data = []
    if results['metadatas']:
        for i in range(len(results['metadatas'][0])):
            retrieved_data.append({
                "id": results['ids'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })

    return retrieved_data

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    
    # Mock competency profile (similar to Agent 1 output)
    mock_profile = {
        "user_id": "test_user_123",
        "competencies": [
            {"name": "Python", "level": "bajo", "score": 0.3},
            {"name": "SQL Databases", "level": "bajo", "score": 0.2},
            {"name": "Frontend", "level": "alto", "score": 0.9}
        ]
    }
    
    print("--------------------------------------------------")
    print("          TESTING RAG RETRIEVER IN CONSOLE        ")
    print("--------------------------------------------------")
    
    # Test with gaps
    mock_gaps = [{"name": "Advanced Python"}, {"name": "Data Architecture"}]
    matches = retrieve_relevant_courses(mock_profile, gaps=mock_gaps)
    
    print(f"\n[SUCCESS] Found {len(matches)} relevant courses:")
    for match in matches:
        print(f"- {match['metadata']['title']} (Level: {match['metadata']['level']})")
