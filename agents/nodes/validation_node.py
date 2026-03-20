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

from agents.schemas.validation_schema import ValidationResult
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

def validate_roadmap(roadmap_dict: dict, competency_profile_dict: dict) -> dict:
    """
    Validates a generated roadmap against the user's competency profile and taxonomy rules.
    """
    
    # 1. Configure the LLM "Brain"
    llm = ChatGroq(
        # We need a slightly more reasoning-capable model for validation
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_retries=2
    )
    
    # 2. Enforce Output Structure via Pydantic
    structured_llm = llm.with_structured_output(ValidationResult)
    
    # 3. Build the Prompt Template
    system_instructions = load_skill_prompt("validation_skill")
    taxonomy_data = _load_taxonomy_str()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("system", "OFFICIAL COMPETENCY TAXONOMY JSON:\n{taxonomy}"),
        ("human", "Audit this generated learning roadmap based on the user's current profile.\n"
                  "Current Competency Profile:\n{profile}\n\n"
                  "Generated Roadmap to Audit:\n{roadmap}")
    ])
    
    # 4. Connect the pipeline
    validation_chain = prompt | structured_llm
    
    print(f"\n[INFO] [Node: Validation] Starting Audit for Roadmap ID: {roadmap_dict.get('roadmap_id')}...")
    
    # 5. Execute Inference with centralized Guardrails
    try:
        response_model = validation_chain.invoke({
            "taxonomy": taxonomy_data,
            "profile": json.dumps(competency_profile_dict, ensure_ascii=False),
            "roadmap": json.dumps(roadmap_dict, ensure_ascii=False)
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
    mock_profile = {
        "user_id": "usr_123",
        "profile_id": "prf_1",
        "competencies": [
            {"competency_id": "python", "name": "Python", "level": "ninguno", "score": 0.0}
        ],
        "recommended_approach": "GENERALISTA",
        "summary": "Mock profile"
    }
    
    mock_roadmap = {
        "roadmap_id": "rm_test",
        "user_id": "usr_123",
        "trajectory_a": {
            "approach": "GENERALISTA",
            "phases": [
                {
                    "phase_order": 1,
                    "name": "Phase 1 - Expert",
                    "blocks": [
                        {"block_id": "blk_1", "content_id": "ml-301", "title": "Machine Learning Avanzado", "order": 1, "completed": False}
                    ]
                }
            ],
            "summary": "Bad roadmap test"
        },
        "trajectory_b": {
            "approach": "ESPECIALISTA",
            "phases": [],
            "summary": "Empty"
        }
    }
    
    final_output = validate_roadmap(mock_roadmap, mock_profile)
    print("\n[SUCCESS] FINAL OUTPUT:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
