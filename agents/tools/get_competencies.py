import json
import os
from langchain_core.tools import tool

@tool
def get_competencies() -> str:
    """
    Reads and returns the official competency taxonomy from competencies.json.
    Use this to ensure you only use valid competency IDs.
    """
    # Base directory for the agents package
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "competencies.json")
    
    try:
        if not os.path.exists(path):
            return "Error: competencies.json not found."
            
        with open(path, "r", encoding="utf-8") as f:
            competencies = json.load(f)
            return json.dumps(competencies, ensure_ascii=False)
    except Exception as e:
        return f"Error reading competencies: {str(e)}"
