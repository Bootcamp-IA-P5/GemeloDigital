import os
import sys
import json
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Fix Python Path
current_dir = os.path.dirname(os.path.abspath(__file__)) # agents/nodes
root_dir = os.path.dirname(os.path.dirname(current_dir)) # project root
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agents.schemas.gap_schema import GapAnalysisResult
from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response
from agents.utils.prompt_loader import load_skill_prompt

load_dotenv()

BASE_DIR = root_dir
TAXONOMY_PATH = os.path.join(BASE_DIR, "agents", "data", "competencies.json")

def _load_taxonomy_str() -> str:
    """Reads the official 25 competencies dictionary."""
    try:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read taxonomy at {TAXONOMY_PATH}: {error}")
        return "{}"

def calculate_gaps(competency_profile_dict: dict, user_answers_json: str, original_user_id: str) -> dict:
    """
    Compares the current user profile against the target role derived from user_answers_json.
    """
    
    # 1. Configure the LLM "Brain"
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_retries=2
    )
    
    # 2. Enforce Output Structure via Pydantic
    structured_llm = llm.with_structured_output(GapAnalysisResult)
    
    # 3. Build the Prompt Template
    system_instructions = load_skill_prompt("gap_analysis_skill")
    taxonomy_data = _load_taxonomy_str()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("system", "OFFICIAL COMPETENCY TAXONOMY JSON:\n{taxonomy}"),
        ("human", "Analyze the user's current profile and target expectations.\n"
                  "User_Id: {user_id}\n"
                  "Questionnaire Answers (for target role context):\n{raw_answers}\n"
                  "Current Competency Profile:\n{profile}")
    ])
    
    # 4. Connect the pipeline
    gap_chain = prompt | structured_llm
    
    print(f"\n[INFO] [Node: Gap Analyzer] Starting Analysis for: {original_user_id}...")
    
    # 5. Execute Inference with centralized Guardrails
    try:
        response_model = gap_chain.invoke({
            "taxonomy": taxonomy_data,
            "user_id": original_user_id,
            "raw_answers": user_answers_json,
            "profile": json.dumps(competency_profile_dict, ensure_ascii=False)
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
        "currentRole": "Junior Frontend dev",
        "targetRole": "FullStack developer",
        "experience": 2
    }, ensure_ascii=False)
    
    mock_profile = {
        "user_id": "usr_123",
        "profile_id": "prf_1",
        "competencies": [
            {"competency_id": "web-development", "name": "Desarrollo Web", "level": "alto", "score": 0.9},
            {"competency_id": "javascript", "name": "JavaScript", "level": "medio", "score": 0.6}
        ],
        "recommended_approach": "GENERALISTA",
        "summary": "Mock profile"
    }
    
    final_output = calculate_gaps(mock_profile, mock_frontend_answers, "usr_123")
    print("\n[SUCCESS] FINAL OUTPUT:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
