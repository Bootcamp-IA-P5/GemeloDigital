from typing import List, Optional
from pydantic import BaseModel, Field

class RoadmapBlock(BaseModel):
    """
    Represents a single learning unit (course) within a phase.
    """
    block_id: str = Field(..., description="Unique ID for this block (e.g., 'blk_001')")
    content_id: str = Field(..., description="The original Course ID from the catalog/RAG results")
    title: str = Field(..., description="Title of the course IN SPANISH")
    order: int = Field(..., description="Order of the course within its phase (1, 2, 3...)")
    completed: bool = Field(default=False, description="Whether the user has finished this course")

class RoadmapPhase(BaseModel):
    """
    Represents a logical stage in the learning journey.
    """
    phase_order: int = Field(..., description="Global order of the phase (1, 2, 3...)")
    name: str = Field(..., description="Name of the phase IN SPANISH (e.g., 'Fundamentos', 'Especialización')")
    blocks: List[RoadmapBlock] = Field(default_factory=list, description="List of courses in this phase")

class RoadmapStructure(BaseModel):
    """
    The structured output produced by the Planning Agent (Agent 2).
    """
    roadmap_id: str = Field(..., description="Unique ID for the roadmap (e.g., 'rm_xyz')")
    user_id: str = Field(..., description="The ID of the user this roadmap belongs to")
    approach: str = Field(..., description="Trajectory type: 'GENERALISTA' or 'ESPECIALISTA'")
    phases: List[RoadmapPhase] = Field(default_factory=list, description="Ordered phases of the curriculum")
    
    # We include this field so the Planning Agent can provide a preliminary rationale,
    # which will then be refined or replaced by the Explanatory Agent (Agent 3).
    explanation: str = Field(
        ..., 
        description="A professional summary IN SPANISH explaining why this roadmap was designed this way."
    )
