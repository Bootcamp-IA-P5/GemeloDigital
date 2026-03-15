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

# 1. Imports from our new structure
from agents.schemas.profiling_schema import CompetencyProfile
from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response

# Load environment variables
load_dotenv()

# Static paths (updated to reflect movement to nodes/ folder)
# __file__ is in agents/nodes/profiling_node.py
# Reference data and prompts using absolute project root logic
BASE_DIR = root_dir
TAXONOMY_PATH = os.path.join(BASE_DIR, "agents", "data", "competencies.json")
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "profiling_prompt.md")

def _load_taxonomy_str() -> str:
    """Reads the official 25 competencies dictionary."""
    try:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read taxonomy at {TAXONOMY_PATH}: {error}")
        return "{}"

def _load_system_prompt() -> str:
    """Reads the strict instructional prompt."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read prompt at {PROMPT_PATH}: {error}")
        return "You are a helpful assistant."

def generate_cognitive_profile(user_answers_json: str, original_user_id: str) -> dict:
    """
    Transforms noisy web form data into perfectly validated JSON using AI.
    """
    
    # 2. Configure the LLM "Brain"
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_retries=2
    )
    
    # 3. Enforce Output Structure via Pydantic
    structured_llm = llm.with_structured_output(CompetencyProfile)
    
    # 4. Build the Prompt Template
    system_instructions = _load_system_prompt()
    taxonomy_data = _load_taxonomy_str()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("system", "OFFICIAL COMPETENCY TAXONOMY JSON:\n{taxonomy}"),
        ("human", "Analyze this user form and return my profile JSON.\nUser_Id={user_id}\nRaw_Answers:\n{raw_answers}")
    ])
    
    # 5. Connect the pipeline
    profiling_chain = prompt | structured_llm
    
    print(f"\n[INFO] [Node: Profiling] Starting Analysis for: {original_user_id}...")
    
    # 6. Execute Inference with centralized Guardrails
    try:
        response_model = profiling_chain.invoke({
            "taxonomy": taxonomy_data,
            "user_id": original_user_id,
            "raw_answers": user_answers_json
        })
        
        # Use centralized validation and formatting
        return validate_and_format_response(response_model)
        
    except Exception as error:
        # Use centralized error handler
        return handle_llm_output_error(error)

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    mock_frontend_answers = json.dumps({
        "q1_role": "Junior Frontend dev",
        "q2_skills": "HTML/CSS expert, but no experience in Python or AI.",
        "q3_goal": "I want to be a FullStack developer."
    }, ensure_ascii=False)
    
    test_user = "usr_refactor_test"
    
    print("--------------------------------------------------")
    print("      TESTING REFACTORED PROFILING NODE           ")
    print("--------------------------------------------------")
    
    final_output = generate_cognitive_profile(mock_frontend_answers, test_user)
    print("\n[SUCCESS] FINAL OUTPUT:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
