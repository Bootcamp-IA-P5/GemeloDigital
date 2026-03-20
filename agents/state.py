from typing import TypedDict, List, Optional, Any, Annotated
import operator

class AgentState(TypedDict):
    """
    The Global State for our 7-node LangGraph workflow.
    """
    # 0. Input
    user_id: str
    raw_answers: str # Complete questionnaire JSON
    
    # 1. Profiling & Gaps
    # Result of profiling_node (structured user data)
    competency_profile: Optional[dict] = None
    # Result of gap_analyzer_node (ordered by impact)
    prioritized_gaps: List[dict] = []
    
    # 2. RAG Retrieval
    # Courses from ChromaDB matching the gaps
    retrieved_courses: List[dict] = []
    
    # 3. Planning & Validation
    # Output of planning_node (Trajectories A & B)
    roadmap: Optional[dict] = None
    # Feedback from validation_node if inconsistencies are found
    validation_feedback: Annotated[List[str], operator.add] = []
    
    # 4. Explanations & ML
    # Output of explanatory_node (The 'why' for each block)
    explanations: Optional[dict] = None
    # Output of ml_prediction_node ('A' or 'B')
    ml_prediction: Optional[str] = None
    
    # 5. Infrastructure & Metadata
    # Accumulated errors during execution
    errors: Annotated[List[str], operator.add] = []
    # Tracking for conditional edges
    next_step: Optional[str] = None
