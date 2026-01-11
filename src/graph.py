from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from backend.src.models import AgentState
from backend.src.prompts import TRIAGE_SYSTEM_PROMPT, CRISIS_RESPONSE
from backend.src.services.qdrant import check_recurrence, save_memory
from backend.src.services.calendar import find_therapists, book_appointment

llm = ChatOpenAI(model="gpt-4o")

# --- Nodes ---

def triage_node(state: AgentState):
    """Analyzes input, checks Qdrant for history, determines flow."""
    last_message = state["messages"][-1].content
    
    # 1. Check Memory (Qdrant)
    similar_issues = check_recurrence(state["user_id"], last_message)
    recurrence_count = state.get("recurrence_count", 0) + len(similar_issues)
    
    # 2. LLM Analysis (Simplified for brevity)
    # In reality, you'd use structured output to get a classification
    response = llm.invoke([
        {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
        {"role": "user", "content": last_message}
    ])
    
    # Simple keyword heuristic for this example
    severity = "normal"
    if "suicide" in last_message.lower() or "kill" in last_message.lower():
        severity = "crisis"
    elif recurrence_count > 3:
        severity = "concerning"

    return {
        "messages": [response], 
        "sentiment_score": 0.5, # Placeholder
        "recurrence_count": recurrence_count,
        "booking_step": "none" if severity != "concerning" else "ask_intent"
    }

def crisis_node(state: AgentState):
    return {"messages": [{"role": "assistant", "content": CRISIS_RESPONSE}]}

def scheduler_node(state: AgentState):
    """Handles the multi-turn logic of booking."""
    step = state.get("booking_step")
    data = state.get("booking_data", {})
    last_msg = state["messages"][-1].content

    if step == "ask_intent":
        msg = "I've noticed this has been bothering you for a while. Would you like to speak with a professional therapist? (Yes/No)"
        return {"booking_step": "wait_intent_answer", "messages": [msg]}
    
    elif step == "wait_intent_answer":
        if "yes" in last_msg.lower():
            msg = "Okay. Please select a time slot: [Tomorrow 10am, Tomorrow 2pm]. Also, do you prefer a specific gender or proximity?"
            return {"booking_step": "wait_details", "messages": [msg]}
        else:
            msg = "I understand. I'm here to listen."
            return {"booking_step": "none", "messages": [msg]}

    elif step == "wait_details":
        # Simulate logic to parse input and call GCal
        # In production: Use an extraction chain here
        success = book_appointment(data)
        msg = "Appointment confirmed! I've sent the invite to your Google Calendar."
        return {"booking_step": "done", "messages": [msg]}

    return {"booking_step": "none"}

# --- Conditional Logic ---

def route_triage(state: AgentState) -> Literal["crisis", "scheduler", "end"]:
    last_content = state["messages"][-1].content
    if state.get("booking_step") == "ask_intent":
        return "scheduler"
    if "crisis" in last_content.lower(): # Or based on classification
        return "crisis"
    return "end" # Just a normal chat reply

def route_scheduler(state: AgentState):
    if state["booking_step"] in ["done", "none"]:
        return "end"
    return "wait_input" # Wait for user reply in chainlit

# --- Graph Construction ---

workflow = StateGraph(AgentState)

workflow.add_node("triage", triage_node)
workflow.add_node("crisis", crisis_node)
workflow.add_node("scheduler", scheduler_node)

workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    route_triage,
    {
        "crisis": "crisis",
        "scheduler": "scheduler",
        "end": END
    }
)

# If we are in the scheduler loop, we might return to END to wait for user input
# or loop back to scheduler to process the next step
workflow.add_edge("scheduler", END)
workflow.add_edge("crisis", END)

app_graph = workflow.compile()