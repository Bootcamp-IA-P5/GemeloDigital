from typing import TypedDict, List, Optional, Any
import operator

class AgentState(TypedDict):
    """
    The Global State for our LangGraph workflow.
    This "suitcase" carries all the information through the agents.
    """
    # Input from the user
    user_id: str
    raw_answers: str
    
    # 1. Profiling Agent Result (Output of Agent 1)
    # We store the dictionary version of our CompetencyProfile schema
    competency_profile: Optional[dict] = None
    
    # 2. RAG Retrieval Result
    # List of courses found in ChromaDB that match the gaps
    retrieved_courses: List[dict] = []
    
    # 3. Planning Agent Result (Output of Agent 2)
    # The structured roadmap before the explanations
    roadmap: Optional[dict] = None
    
    # 4. Final Recommendation (ML Model Output)
    # Predicted path: 'A' (Generalist) or 'B' (Specialist)
    ml_recommended_path: Optional[str] = None
    
    # 5. Infrastructure and Safety
    # List of logs or error messages for the external guardrails
    # Annotated with operator.add so errors accumulate instead of overwriting
    errors: List[str] = []
    
    # Metadata for tracking state progression
    next_step: Optional[str] = None
