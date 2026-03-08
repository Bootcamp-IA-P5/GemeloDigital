import os
import sys
import json
from dotenv import load_dotenv

# Fix Python Path
# This allows running the script directly: python3 agents/profiling_agent.py
# by adding the project root to the system path.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException

# 1. Import our strict Pydantic schemas
from agents.schemas.profiling_schema import CompetencyProfile

# Load environment variables from the root .env file
load_dotenv()

# Static paths for the official Taxonomy and the HR Prompt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(BASE_DIR, "agents", "data", "competencies.json")
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "profiling_prompt.txt")

def _load_taxonomy_str() -> str:
    """Reads the official 25 competencies dictionary to provide it to the LLM."""
    try:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read taxonomy: {error}")
        return "{}"

def _load_system_prompt() -> str:
    """Reads the strict instructional prompt from the text file."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read prompt: {error}")
        return "You are a helpful assistant."

def generate_cognitive_profile(user_answers_json: str, original_user_id: str) -> dict:
    """
    Core function for Agent 1 (Profiling).
    Transforms noisy web form data into perfectly validated JSON using AI.
    """
    
    # 2. Configure the LLM "Brain"
    # llama-3.1-8b-instant on Groq for ultra-fast inference.
    # GUARDRAIL 1: Temperature 0.1 prevents creative hallucinations.
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_retries=2 # Groq handles internal network retries
    )
    
    # 3. Enforce Output Structure via Pydantic
    # GUARDRAIL 2: Langchain enforces adherence to our schema.
    structured_llm = llm.with_structured_output(CompetencyProfile)
    
    # 4. Build the Prompt Template
    system_instructions = _load_system_prompt()
    taxonomy_data = _load_taxonomy_str()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("system", f"OFFICIAL COMPETENCY TAXONOMY JSON:\n{taxonomy_data}"),
        ("human", "Analyze this user form and return my profile JSON.\nUser_Id={user_id}\nRaw_Answers:\n{raw_answers}")
    ])
    
    # 5. Connect the pipeline (Prompt -> LLM with Pydantic)
    profiling_chain = prompt | structured_llm
    
    print(f"\n[INFO] Starting Cognitive Analysis for user: {original_user_id}...")
    
    # 6. Execute Inference
    try:
        # The magic happens here (token consumption)
        response_model = profiling_chain.invoke({
            "user_id": original_user_id,
            "raw_answers": user_answers_json
        })
        
        # Convert the Pydantic Python object back to a raw dictionary (JSON format) for the Backend (Role 1)
        return response_model.model_dump()
        
    except OutputParserException as error:
        # GUARDRAIL 3: Safety net if the LLM refuses to return valid JSON.
        print(f"[FATAL] Agent Output Parser Error: The LLM disobeyed and broke the JSON schema.\n{error}")
        return {"error": "The Profiling Agent failed to structure the user data. Parsing exception."}
    except Exception as error:
        # GUARDRAIL 4: Network drops or missing Groq API Key.
        print(f"[FATAL] Groq API System Error: {error}")
        return {"error": "Cognitive analysis service is temporarily unavailable."}

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    
    # A fake JSON simulating what the Frontend (Role 3) would send to the API (Role 1)
    mock_frontend_answers = json.dumps({
        "q1_role": "Soy programadora frontend hace un par de años.",
        "q2_skills": "Sé maquetar muy bien, pero he empezado a tocar bases de datos este año y solo sé que es un SELECT básico en SQL. De python no tengo ni idea.",
        "q3_goal": "Mi objetivo es convertirme en Data Engineer el año que viene."
    }, ensure_ascii=False)
    
    test_user = "usr_999_test_local"
    
    print("--------------------------------------------------")
    print("          TESTING PROFILING AGENT IN CONSOLE      ")
    print("--------------------------------------------------")
    
    final_output = generate_cognitive_profile(user_answers_json=mock_frontend_answers, original_user_id=test_user)
    
    print("\n[SUCCESS] FINAL VALIDATED OUTPUT FROM AGENT 1:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
