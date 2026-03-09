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

# 1. Imports from our structure
from agents.schemas.planning_schema import RoadmapStructure
from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response

# Load environment variables
load_dotenv()

# Static paths
BASE_DIR = root_dir
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "explanatory_prompt.txt")

def _load_system_prompt() -> str:
    """Reads the pedagogical guides for explanations."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as error:
        print(f"[ERROR] Failed to read explanatory prompt at {PROMPT_PATH}: {error}")
        return "You are a helpful pedagogical coach."

def generate_detailed_explanations(competency_profile: dict, roadmap_dict: dict) -> dict:
    """
    Agent 3: Explanatory Agent.
    Adds personalized justifications for each course in the roadmap.
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
    
    # Prepare the context
    user_summary = json.dumps(competency_profile, indent=2, ensure_ascii=False)
    roadmap_context = json.dumps(roadmap_dict, indent=2, ensure_ascii=False)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", (
            "USER PROFILE:\n{profile}\n\n"
            "CURRENT ROADMAP (NEEDS EXPLANATIONS):\n{roadmap}\n\n"
            "Please justify each course in Spanish."
        ))
    ])
    
    # 5. Connect the pipeline
    explanatory_chain = prompt | structured_llm
    
    print(f"\n[INFO] [Node: Explanatory] Generating personalized justifications for: {competency_profile.get('user_id', 'user')}...")
    
    # 6. Execute Inference
    try:
        response_model = explanatory_chain.invoke({
            "profile": user_summary,
            "roadmap": roadmap_context
        })
        
        return validate_and_format_response(response_model)
        
    except Exception as error:
        return handle_llm_output_error(error)

# ==========================================
# Testing block for console execution
# ==========================================
if __name__ == "__main__":
    # Mock data
    mock_profile = {
        "user_id": "usr_expl_test",
        "competencies": [{"name": "Python", "level": "bajo", "score": 0.2}]
    }
    
    mock_roadmap = {
        "roadmap_id": "rm_test",
        "user_id": "usr_expl_test",
        "approach": "GENERALISTA",
        "phases": [
            {
                "phase_order": 1,
                "name": "Fundamentos",
                "blocks": [
                    {"block_id": "blk_1", "content_id": "crs_1", "title": "Python 101", "order": 1}
                ]
            }
        ],
        "explanation": "Resumen inicial."
    }
    
    print("--------------------------------------------------")
    print("      TESTING EXPLANATORY AGENT NODE              ")
    print("--------------------------------------------------")
    
    final_output = generate_detailed_explanations(mock_profile, mock_roadmap)
    print("\n[SUCCESS] ROADMAP WITH DETAILED EXPLANATIONS:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
