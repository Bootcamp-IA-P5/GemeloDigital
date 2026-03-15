from typing import List
from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    """
    Result of the Validation Agent's check on the Roadmap.
    """
    is_valid: bool = Field(
        ..., 
        description="True if the roadmap is pedagogically sound and logically consistent, False otherwise."
    )
    feedback: List[str] = Field(
        default_factory=list,
        description="If is_valid is False, provide a list of specific, ACTIONABLE errors found in the roadmap IN SPANISH (e.g., 'El curso X requiere conocimientos previos de Y.'). Leave empty if is_valid is True."
    )
