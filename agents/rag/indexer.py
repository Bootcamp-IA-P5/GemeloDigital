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


def reindex_course(course: dict) -> dict:
    """
    Re-indexa un solo curso en ChromaDB.
    Se invoca cuando el admin edita un curso desde el panel.

    Args:
        course: dict con los campos del curso (id, title, description,
                competencies, level, url, etc.)

    Returns:
        dict con {"status": "ok", "course_id": ...}
        o {"status": "error", "detail": ...}
    """
    try:
        course_id = course.get("id", "unknown_id")
        title = course.get("title", "")
        description = course.get("description", "")
        level = course.get("level", "beginner")
        competencies = course.get("competencies", [])
        competencies_str = ", ".join(competencies)

        # Misma lógica de text_to_embed que index_courses()
        text_to_embed = f"Title: {title}. Description: {description}. Competencies: {competencies_str}. Level: {level}."

        # Calcular embedding
        embedding = embedding_model.encode([text_to_embed]).tolist()

        # Upsert en ChromaDB (actualiza si existe, inserta si no)
        collection.upsert(
            ids=[course_id],
            documents=[text_to_embed],
            embeddings=embedding,
            metadatas=[{
                "title": title,
                "level": level,
                "competencies": competencies_str,
                "url": course.get("url", "")
            }]
        )

        print(f"[SUCCESS] Curso '{course_id}' re-indexado correctamente.")
        return {"status": "ok", "course_id": course_id}

    except Exception as e:
        print(f"[ERROR] Fallo al re-indexar curso: {e}")
        return {"status": "error", "detail": str(e)}


def delete_course_embedding(course_id: str) -> dict:
    """
    Elimina el embedding de un curso de ChromaDB.
    Se invoca cuando el admin elimina un curso del catálogo.

    Args:
        course_id: ID del curso a eliminar.

    Returns:
        dict con {"status": "ok"} o {"status": "error", "detail": ...}
    """
    try:
        # Verificar que existe antes de intentar eliminar
        existing = collection.get(ids=[course_id])
        if not existing["ids"]:
            return {"status": "ok", "detail": f"Curso '{course_id}' no existía en ChromaDB (noop)."}

        collection.delete(ids=[course_id])
        print(f"[SUCCESS] Embedding del curso '{course_id}' eliminado de ChromaDB.")
        return {"status": "ok", "course_id": course_id}

    except Exception as e:
        print(f"[ERROR] Fallo al eliminar embedding: {e}")
        return {"status": "error", "detail": str(e)}


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
