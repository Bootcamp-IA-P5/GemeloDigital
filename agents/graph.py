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
from agents.nodes.planning_node import generate_roadmap
from agents.rag.retriever import retrieve_relevant_courses

# ==========================================
# 1. NODE DEFINITIONS (The Workers)
# ==========================================

def profiling_node(state: AgentState):
    """
    Invokes the Profiling Agent to convert raw answers into a structured profile.
    """
    print("\n--- [NODE] Profiling Agent ---")
    
    profile_dict = generate_cognitive_profile(
        user_answers_json=state["raw_answers"],
        original_user_id=state["user_id"]
    )
    
    # Simple External Guardrail: Check if the LLM returned an error
    if "error" in profile_dict:
        return {
            "errors": [f"Profiling Error: {profile_dict['error']}"],
            "next_step": "end"
        }
    
    return {
        "competency_profile": profile_dict,
        "next_step": "retrieve"
    }

def retrieval_node(state: AgentState):
    """
    Search for relevant courses in ChromaDB using the generated profile.
    """
    print("\n--- [NODE] RAG Retrieval ---")
    
    if not state["competency_profile"]:
        return {"errors": ["No competency profile found to perform retrieval."]}
    
    courses = retrieve_relevant_courses(state["competency_profile"])
    
    return {
        "retrieved_courses": courses,
        "next_step": "plan" 
    }

def planning_node(state: AgentState):
    """
    Invokes the Planning Agent to design the roadmap based on profile and courses.
    """
    print("\n--- [NODE] Planning Agent ---")
    
    if not state["competency_profile"] or not state["retrieved_courses"]:
        return {"errors": ["Missing profile or courses to design roadmap."]}
    
    roadmap_dict = generate_roadmap(
        competency_profile=state["competency_profile"],
        retrieved_courses=state["retrieved_courses"]
    )
    
    if "error" in roadmap_dict:
        return {"errors": [f"Planning Error: {roadmap_dict['error']}"]}
        
    return {
        "roadmap": roadmap_dict,
        "next_step": "explain" # Next will be Agent 3 (Explanatory)
    }

# ==========================================
# 2. GRAPH CONSTRUCTION (The Roadmap)
# ==========================================

# Initialize the Graph with our State schema
workflow = StateGraph(AgentState)

# Add our nodes to the graph
workflow.add_node("profiler", profiling_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("planner", planning_node)

# Define the flow (Edges)
workflow.set_entry_point("profiler")

# Logic to choose next step or end
workflow.add_edge("profiler", "retriever")
workflow.add_edge("retriever", "planner")
workflow.add_edge("planner", END)

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
