import os
import sys
import json
from typing import Literal

# Fix Python Path to allow running from root
current_dir = os.path.dirname(os.path.abspath(__file__)) # agents/
root_dir = os.path.dirname(current_dir) # project root
if root_dir not in sys.path:
    sys.path.append(root_dir)

from langgraph.graph import StateGraph, END
from agents.state import AgentState

# Import our specialized modules
from agents.nodes.profiling_node import generate_cognitive_profile
from agents.nodes.gap_analyzer_node import calculate_gaps
from agents.rag.retriever import retrieve_relevant_courses
from agents.nodes.planning_node import generate_roadmap
from agents.nodes.validation_node import validate_roadmap
from agents.nodes.explanatory_node import generate_detailed_explanations
from agents.nodes.ml_prediction_node import predict_trajectory

# ==========================================
# 1. NODE DEFINITIONS (The Workers)
# ==========================================

def profiling_node(state: AgentState):
    """
    Invokes the Profiling Agent to convert raw answers into a structured profile.
    """
    print("\n--- [NODE] Profiling Agent ---")
    
    profile_dict = generate_cognitive_profile(
        user_answers_json=state.get("raw_answers", "{}"),
        original_user_id=state.get("user_id", "usr_unknown")
    )
    
    # Simple External Guardrail: Check if the LLM returned an error
    if "error" in profile_dict:
        return {
            "errors": [f"Profiling Error: {profile_dict['error']}"],
            "next_step": "end"
        }
    
    return {
        "competency_profile": profile_dict,
        "next_step": "gap"
    }

def gap_analyzer_node(state: AgentState):
    """
    Invokes the Gap Analyzer to compare profile vs target role.
    """
    print("\n--- [NODE] Gap Analyzer ---")
    
    if not state.get("competency_profile"):
        return {"errors": ["No competency profile found to analyze gaps."]}
        
    gaps_result = calculate_gaps(
        competency_profile_dict=state["competency_profile"],
        user_answers_json=state["raw_answers"],
        original_user_id=state["user_id"]
    )
    
    if "error" in gaps_result:
        return {"errors": [f"Gap Analysis Error: {gaps_result['error']}"]}
        
    return {
        "prioritized_gaps": gaps_result.get("prioritized_gaps", []),
        "next_step": "retrieve"
    }

def retrieval_node(state: AgentState):
    """
    Search for relevant courses in ChromaDB using the generated profile.
    """
    print("\n--- [NODE] RAG Retrieval ---")
    
    if not state.get("competency_profile"):
        return {"errors": ["No competency profile found to perform retrieval."]}
    
    courses = retrieve_relevant_courses(
        competency_profile=state.get("competency_profile", {}),
        gaps=state.get("prioritized_gaps", [])
    )
    
    return {
        "retrieved_courses": courses,
        "next_step": "plan" 
    }

def planning_node(state: AgentState):
    """
    Invokes the Planning Agent to design the roadmap based on profile and courses.
    """
    print("\n--- [NODE] Planning Agent ---")
    
    if not state.get("competency_profile") or not state.get("retrieved_courses"):
        return {"errors": ["Missing profile or courses to design roadmap."]}
    
    roadmap_dict = generate_roadmap(
        competency_profile=state.get("competency_profile"),
        retrieved_courses=state.get("retrieved_courses")
    )
    
    if "error" in roadmap_dict:
        return {"errors": [f"Planning Error: {roadmap_dict['error']}"]}
        
    return {
        "roadmap": roadmap_dict,
        "next_step": "validate" 
    }

def validation_node(state: AgentState):
    """
    Audits the generated roadmap. If invalid, routes back to planning.
    """
    print("\n--- [NODE] Validation Agent ---")
    
    if not state.get("roadmap") or not state.get("competency_profile"):
        return {"errors": ["Missing roadmap or profile for validation."]}
        
    validation_result = validate_roadmap(
        roadmap_dict=state["roadmap"],
        competency_profile_dict=state["competency_profile"]
    )
    
    if "error" in validation_result:
        return {"errors": [f"Validation Error: {validation_result['error']}"]}
        
    is_valid = validation_result.get("is_valid", False)
    feedback = validation_result.get("feedback", [])
    
    # We use a simple retry counter by checking how many feedbacks we have added.
    # If the feedback list is getting too large, we might want to force proceed to avoid infinite loops.
    # But for now, we just route back.
    
    return {
        "validation_feedback": feedback,
        "next_step": "explain" if is_valid else "plan"
    }

def explanatory_node(state: AgentState):
    """
    Invokes the Explanatory Agent to add personalized justifications to the roadmap.
    """
    print("\n--- [NODE] Explanatory Agent ---")
    
    if not state.get("competency_profile") or not state.get("roadmap"):
        return {"errors": ["Missing profile or roadmap to generate explanations."]}
    
    final_roadmap = generate_detailed_explanations(
        competency_profile=state.get("competency_profile"),
        roadmap_dict=state.get("roadmap")
    )
    
    if "error" in final_roadmap:
        return {"errors": [f"Explanation Error: {final_roadmap['error']}"]}
        
    return {
        "roadmap": final_roadmap,
        "next_step": "ml_predict"
    }

def ml_predict_node(state: AgentState):
    """
    Assigns the optimal trajectory classification (A/B) to the state.
    """
    print("\n--- [NODE] ML Predictor ---")
    
    if not state.get("competency_profile"):
        return {"errors": ["Missing profile for ML prediction."]}
        
    prediction_result = predict_trajectory(state["competency_profile"])
    
    return {
        "ml_prediction": prediction_result.get("ml_prediction", "A"),
        "next_step": "end"
    }

# ==========================================
# 2. GRAPH CONSTRUCTION (The Roadmap)
# ==========================================

# Initialize the Graph with our State schema
workflow = StateGraph(AgentState)

# Add our nodes to the graph
workflow.add_node("profiler", profiling_node)
workflow.add_node("gap_analyzer", gap_analyzer_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("planner", planning_node)
workflow.add_node("validator", validation_node)
workflow.add_node("explainer", explanatory_node)
workflow.add_node("ml_predictor", ml_predict_node)

# Define the flow (Edges)
workflow.set_entry_point("profiler")

# Conditional Router Function
def route_next_step(state: AgentState):
    step = state.get("next_step")
    if state.get("errors") and step == "end":
        return "end"
    if step is None or step == "end":
        return "end"
    return str(step)

workflow.add_edge("profiler", "gap_analyzer")
workflow.add_edge("gap_analyzer", "retriever")
workflow.add_edge("retriever", "planner")
workflow.add_edge("planner", "validator")

# Conditional Edge from Validator
workflow.add_conditional_edges(
    "validator",
    route_next_step,
    {
        "plan": "planner",
        "explain": "explainer",
        "end": END
    }
)

workflow.add_edge("explainer", "ml_predictor")
workflow.add_edge("ml_predictor", END)

# Compile the graph
app = workflow.compile()

# ==========================================
# 3. Testing block for console execution
# ==========================================
if __name__ == "__main__":
    
    # Mock data for testing the whole flow
    initial_input = {
        "user_id": "usr_demo_graph",
        "raw_answers": json.dumps({
            "q1": "I am a junior python developer",
            "q2": "I want to learn about large language models and RAG",
            "q3": "I don't know anything about vector databases"
        })
    }
    
    print("--------------------------------------------------")
    print("          TESTING LANGGRAPH WORKFLOW              ")
    print("--------------------------------------------------")
    
    # Run the graph
    for output in app.stream(initial_input):
        # Stream the output of each node
        for key, value in output.items():
            print(f"Finished Node: {key}")
            # print(value)
    
    print("\n--------------------------------------------------")
    print("          WORKFLOW COMPLETED                      ")
    print("--------------------------------------------------")
