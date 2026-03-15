import os
import sys
import json
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Fix Python Path to allow running this node in isolation
current_dir = os.path.dirname(os.path.abspath(__file__)) # agents/nodes
root_dir = os.path.dirname(os.path.dirname(current_dir)) # project root
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 1. Imports from our structure
from agents.schemas.planning_schema import RoadmapStructure
from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response

# Load environment variables
load_dotenv()

# Static paths
BASE_DIR = root_dir
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "planning_prompt.md")

def _load_system_prompt() -> str:
    """Reads the pedagogical instructional prompt."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read planning prompt at {PROMPT_PATH}: {error}")
        return "You are a pedagogical expert."

def generate_roadmap(competency_profile: dict, retrieved_courses: list) -> dict:
    """
    Agent 2: Planning Agent.
    Orchestrates the creation of a learning roadmap based on gaps and catalog data.
    """
    
    # 2. Configure the LLM "Brain"
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_retries=2
    )
    
    # 3. Enforce Output Structure via Pydantic
    structured_llm = llm.with_structured_output(RoadmapStructure)
    
    # 4. Build the Prompt Template
    system_instructions = _load_system_prompt()
    
    # Prepare the context for the LLM
    user_id = competency_profile.get("user_id", "unknown_user")
    competency_summary = json.dumps(competency_profile, indent=2, ensure_ascii=False)
    courses_context = json.dumps(retrieved_courses, indent=2, ensure_ascii=False)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", (
            "USER PROFILE:\n{profile}\n\n"
            "AVAILABLE COURSES (RAG):\n{courses}\n\n"
            "Create a roadmap for user {user_id}."
        ))
    ])
    
    # 5. Connect the pipeline
    planning_chain = prompt | structured_llm
    
    print(f"\n[INFO] [Node: Planning] Designing roadmap for user: {user_id}...")
    
    # 6. Execute Inference
    try:
        response_model = planning_chain.invoke({
            "user_id": user_id,
            "profile": competency_summary,
            "courses": courses_context
        })
        
        return validate_and_format_response(response_model)
        
    except Exception as error:
        return handle_llm_output_error(error)

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    # Mock data to simulate the state from previous nodes
    mock_profile = {
        "user_id": "usr_test_planning",
        "approach": "GENERALISTA",
        "competencies": [
            {"name": "Python", "level": "bajo", "score": 0.2},
            {"name": "Bases de datos", "level": "bajo", "score": 0.3}
        ]
    }
    
    mock_courses = [
        {
            "id": "crs_python_101",
            "metadata": {"title": "Python para Principiantes", "level": "beginner"}
        },
        {
            "id": "crs_sql_basic",
            "metadata": {"title": "Introducción a SQL", "level": "beginner"}
        }
    ]
    
    print("--------------------------------------------------")
    print("      TESTING PLANNING AGENT NODE                 ")
    print("--------------------------------------------------")
    
    final_output = generate_roadmap(mock_profile, mock_courses)
    print("\n[SUCCESS] FINAL STRUCTURED ROADMAP:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
