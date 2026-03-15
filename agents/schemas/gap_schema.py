from typing import List, Optional
from pydantic import BaseModel, Field

class CompetencyGap(BaseModel):
    """
    Represents an individual gap detected for a specific competency.
    """
    competency_id: str = Field(
        ..., 
        description="The exact ID of the competency from competencies.json (e.g., 'python', 'sql')."
    )
    name: str = Field(
        ..., 
        description="Readable name of the competency IN SPANISH."
    )
    current_level: str = Field(
        ..., 
        description="Current mastery level ('bajo', 'medio', 'alto' or 'ninguno')."
    )
    target_level: str = Field(
        ..., 
        description="Required mastery level for the target role ('bajo', 'medio', 'alto')."
    )
    gap_score: float = Field(
        ..., 
        description="A calculated numerical gap (e.g., from 0.0 to 1.0) where 1.0 is the highest priority gap."
    )
    impact: str = Field(
        ...,
        description="Impact of this gap on the user's objective ('ALTO', 'MEDIO', 'BAJO')."
    )

class GapAnalysisResult(BaseModel):
    """
    The complete gap analysis result comparing the user profile against their target role.
    """
    user_id: str = Field(
        ..., 
        description="The user_id."
    )
    target_role: str = Field(
        ..., 
        description="The user's target role derived from their questionnaire."
    )
    prioritized_gaps: List[CompetencyGap] = Field(
        default_factory=list,
        description="List of detected gaps, ordered by priority (highest gap_score/impact first)."
    )
    analysis_summary: str = Field(
        ..., 
        description="A short professional summary IN SPANISH analyzing what the user needs to learn most urgently to reach their target role."
    )
