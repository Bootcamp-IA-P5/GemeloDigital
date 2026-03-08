import sys
from langchain_core.exceptions import OutputParserException

def handle_llm_output_error(error: Exception) -> dict:
    """
    Standardizes error reporting for LLM-related failures.
    """
    if isinstance(error, OutputParserException):
        print(f"[FATAL] Agent Output Parser Error: The LLM disobeyed and broke the JSON schema.\n{error}")
        return {"error": "The Agent failed to structure the data. Parsing exception."}
    
    print(f"[FATAL] System Error: {error}")
    return {"error": f"Internal agent error: {str(error)}"}

def validate_and_format_response(response_model) -> dict:
    """
    Converts a Pydantic model response into a raw dictionary for the Backend.
    """
    try:
        return response_model.model_dump()
    except Exception as error:
        return handle_llm_output_error(error)
