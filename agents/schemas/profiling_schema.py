from typing import List
from pydantic import BaseModel, Field

class CompetencyScore(BaseModel):
    """
    Represents an individual user skill detected in the text.
    """
    competency_id: str = Field(
        ..., 
        description="The exact ID of the competency as it appears in the official competencies.json file (e.g., 'python', 'sql'). DO NOT INVENT IDs."
    )
    name: str = Field(
        ..., 
        description="Readable name of the detected competency IN SPANISH."
    )
    level: str = Field(
        ..., 
        description="Current mastery level detected. Must strictly be one of: 'bajo', 'medio' or 'alto'."
    )
    score: float = Field(
        ..., 
        description="Normalized score from 0.0 to 1.0. Example: bajo=0.3, medio=0.6, alto=0.9."
    )

class CompetencyProfile(BaseModel):
    """
    The complete cognitive profile generated after analyzing user answers.
    """
    user_id: str = Field(
        ..., 
        description="The original user_id provided in the request."
    )
    profile_id: str = Field(
        ..., 
        description="A unique ID generated for this analysis (you can invent one if not provided, e.g., 'perf_123')."
    )
    competencies: List[CompetencyScore] = Field(
        default_factory=list,
        description="Exhaustive list of all technical or soft skills detected in the user's answers."
    )
    recommended_approach: str = Field(
        ...,
        description="Based on the profile: If the user lacks basic foundations, choose 'GENERALISTA'. If the user has solid bases and wants to deepen them, choose 'ESPECIALISTA'."
    )
    summary: str = Field(
        ..., 
        description="A short, professional paragraph IN SPANISH summarizing the user's starting point and main objectives. This will be shown to the user."
    )
    avatar_personality: str = Field(
        ...,
        description="A concise description (2-3 sentences) of the avatar's personality based on the user's technical profile (e.g., 'Analítico y apasionado por el detalle')."
    )
    avatar_color: str = Field(
        "blue",
        description="A color that represents the user's profile. Choose from: 'blue', 'purple', 'green', 'orange', 'cyan'."
    )
