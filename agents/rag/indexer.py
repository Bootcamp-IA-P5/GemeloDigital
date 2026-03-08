import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Base Paths Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURSES_FILE = os.path.join(BASE_DIR, "data", "seed", "courses.json")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# 2. Initialize Vector Database (Local ChromaDB) and Model
print("[INFO] Initializing ChromaDB and embedding model...")
# Using a local, lightweight model for text-to-vector embedding
# all-MiniLM-L6-v2 is fast and efficient for local development
embedding_model = SentenceTransformer('all-MiniLM-L6-v2') 
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Create a "collection" (similar to a SQL table) to store courses
collection = client.get_or_create_collection(
    name="courses_collection",
    metadata={"hnsw:space": "cosine"} # Using cosine similarity for semantic matching
)

def index_courses():
    """
    Reads courses from JSON, transforms them into structured text,
    calculates embeddings, and stores them in ChromaDB.
    """
    print(f"[INFO] Reading courses from: {COURSES_FILE}")
    
    if not os.path.exists(COURSES_FILE) or os.path.getsize(COURSES_FILE) == 0:
        print("[WARNING] courses.json does not exist or is empty. Admin (Role 4) must provide data.")
        return

    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as file:
            courses = json.load(file)
    except Exception as error:
        print(f"[ERROR] Failed to load JSON data: {error}")
        return

    print(f"[INFO] Processing {len(courses)} courses...")

    ids = []
    documents = []
    metadatas = []

    for course in courses:
        # A) Extract variables
        course_id = course.get("id", "unknown_id")
        title = course.get("title", "")
        description = course.get("description", "")
        level = course.get("level", "beginner")
        
        # Competencies are expected as a list, e.g., ["python", "sql"]
        competencies = course.get("competencies", [])
        competencies_str = ", ".join(competencies)

        # B) Create the Structured Text Document
        # The AI needs a cohesive string to extract semantic meaning.
        text_to_embed = f"Title: {title}. Description: {description}. Competencies: {competencies_str}. Level: {level}."

        # C) Store in lists for batch processing
        ids.append(course_id)
        documents.append(text_to_embed) 
        metadatas.append({
            "title": title,
            "level": level,
            "competencies": competencies_str, # ChromaDB metadata doesn't support list types natively
            "url": course.get("url", "")
        })

    # D) Calculate vectors and upsert into database
    if documents:
        print("[INFO] Calculating text embeddings (vectors)...")
        # Encodes the text documents into 384-dimensional vectors
        embeddings = embedding_model.encode(documents).tolist()

        print("[INFO] Storing data in ChromaDB...")
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print("[SUCCESS] Indexing completed successfully!")
    else:
        print("[WARNING] No documents found to index.")

if __name__ == "__main__":
    index_courses()
    
    # ---- QUICK CONSOLE TEST ----
    print("\n[TEST] Searching for 'beginner python programming'...")
    query_vector = embedding_model.encode(["beginner python programming"]).tolist()
    
    results = collection.query(
        query_embeddings=query_vector,
        n_results=2
    )
    
    print("\n[RESULTS] Top matches from Database:")
    print(json.dumps(results['metadatas'], indent=2, ensure_ascii=False))
