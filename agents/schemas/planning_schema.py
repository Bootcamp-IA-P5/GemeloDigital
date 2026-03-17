from typing import List, Optional
from pydantic import BaseModel, Field

class RoadmapBlock(BaseModel):
    """A single learning unit (course) within a phase."""
    block_id: str = Field(..., description="Unique ID (e.g., 'blk_001')")
    content_id: str = Field(..., description="Course ID from the catalog")
    title: str = Field(..., description="Course title IN SPANISH")
    explanation: Optional[str] = Field(None, description="Why this course is recommended IN SPANISH")
    order: int = Field(default=1, description="Order within its phase")
    completed: bool = Field(default=False)
    competencies: Optional[List[str]] = Field(default=None, description="Competencies addressed")

class RoadmapPhase(BaseModel):
    """A logical stage in the learning journey (max 3-4 phases)."""
    phase_order: int = Field(..., description="Order of the phase (1, 2, 3)")
    name: str = Field(..., description="Phase name IN SPANISH (e.g., 'Fundamentos')")
    blocks: List[RoadmapBlock] = Field(default_factory=list, description="Courses in this phase (2-4 courses)")

class RoadmapStructure(BaseModel):
    """Complete roadmap output. IMPORTANT: Generate EXACTLY 3 phases, each with 2-3 courses."""
    roadmap_id: str = Field(..., description="Unique ID (e.g., 'rm_user123')")
    user_id: str = Field(..., description="User ID")
    approach: str = Field(default="GENERALISTA", description="GENERALISTA or ESPECIALISTA")
    phases: List[RoadmapPhase] = Field(..., description="EXACTLY 3 phases: Fundamentos, Profundización, Especialización")
    summary: str = Field(default="", description="Brief summary IN SPANISH")
