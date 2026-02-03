"""LangGraph workflow: triage → empathetic reply / scheduler / crisis."""
import os
import json
import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv

from .models import AgentState
from .prompts import TRIAGE_SYSTEM_PROMPT, CRISIS_RESPONSE
from .services.qdrant import check_recurrence, save_memory
from .services.calendar import find_therapists, book_appointment
from .services import store

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)


def _get_content_str(content: any) -> str:
    """Safely extract string content from a message (handling strings and lists)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Handle list of strings or dicts (e.g. from multimodal models)
        parts = []
        for c in content:
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, dict) and "text" in c:
                parts.append(c["text"])
            else:
                parts.append(str(c))
        return " ".join(parts)
    return str(content) if content is not None else ""


def _parse_datetime_with_llm(text: str, history: list = None) -> dict:
    """Use LLM to convert natural language time to ISO format relative to now."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context = ""
    if history:
        # Get last 5 messages for context
        context_msgs = history[-5:]
        context = "Context from previous messages:\n"
        for m in context_msgs:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            msg_text = _get_content_str(m.content)
            context += f"{role}: {msg_text}\n"

    prompt = f"""
    Current date and time: {now_str}
    {context}
    User input: "{text}"
    
    Extract the desired appointment start and end times in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
    Assume a default duration of 1 hour if not specified.
    Return ONLY a JSON object with keys "start_iso" and "end_iso".
    Example: {{"start_iso": "2024-01-01T10:00:00", "end_iso": "2024-01-01T11:00:00"}}
    If no time is specified, return empty strings.
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = _get_content_str(response.content)
        # cleanup markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing date: {e}")
        return {"start_iso": "", "end_iso": ""}


def _parse_severity(content: str) -> str:
    """Extract SEVERITY: normal | concerning | crisis from LLM reply."""
    content = _get_content_str(content)
    if not content:
        return "normal"
    content_lower = content.lower()
    if "severity: crisis" in content_lower or content_lower.strip() == "crisis":
        return "crisis"
    if "severity: concerning" in content_lower:
        return "concerning"
    return "normal"


def _strip_severity_line(content: str) -> str:
    """Remove the SEVERITY: ... line for display."""
    if "SEVERITY:" in content:
        lines = [l for l in content.split("\n") if "SEVERITY:" not in l.upper()]
        return "\n".join(lines).strip()
    return content.strip()


# --- Nodes ---

def triage_node(state: AgentState) -> dict:
    """Analyze message, check recurrence, classify severity, reply or route."""
    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {}
    content = _get_content_str(last_message.content)

    # Check memory (recurrence)
    user_id = state.get("user_id", "")
    similar = check_recurrence(user_id, content)
    recurrence_count = state.get("recurrence_count", 0) + (1 if similar else 0)
    save_memory(user_id, content)

    # LLM triage + empathetic reply (Integrated Safety Check)
    messages = [SystemMessage(content=TRIAGE_SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    if not isinstance(response, AIMessage):
        response = AIMessage(content=str(response))
    reply_content = _get_content_str(response.content)

    # Check for safety refusal from LLM
    if "UNSAFE_INJECTION" in reply_content:
        msg = "I'm sorry, but I can only function as a therapy assistant. I'm here to listen if you'd like to talk about what's on your mind."
        return {
            "messages": [AIMessage(content=msg)],
            "booking_step": "none",
            "severity": "normal"
        }

    severity = _parse_severity(reply_content)
    # Keyword override for crisis
    crisis_words = ["suicide", "kill myself", "end my life", "self-harm", "hurt myself"]
    if "CRISIS" in reply_content or any(w in content.lower() for w in crisis_words):
        severity = "crisis"

    # If user explicitly asked to schedule, go to scheduler (skip ask_intent)
    wants_to_schedule = "schedule" in content.lower() or "book" in content.lower() or "appointment" in content.lower()

    # Preserve wait steps so next user message is routed to scheduler
    current_step = state.get("booking_step", "none")
    if current_step in ("wait_intent", "wait_slots"):
        booking_step = current_step
    elif severity == "crisis":
        booking_step = "none"
    elif wants_to_schedule:
        booking_step = "ask_slots"
    # elif severity == "concerning" and recurrence_count >= 2:
    elif severity == "concerning":
        booking_step = "ask_intent"
    else:
        booking_step = "none"

    # display_content = _strip_severity_line(reply_content)
    display_content = reply_content
    if severity == "crisis":
        display_content = ""  # Will be replaced by crisis node
    # When waiting for booking input, don't add triage reply; scheduler will respond
    if current_step in ("wait_intent", "wait_slots") or booking_step in ("ask_intent", "ask_slots"):
        display_content = ""

    result = {
        "recurrence_count": recurrence_count,
        "booking_step": booking_step,
        "sentiment_score": 0.5,
        "severity": severity,
    }
    if display_content:
        result["messages"] = [AIMessage(content=display_content)]
    
    return result


def crisis_node(state: AgentState) -> dict:
    """Return the fixed crisis hotline message and stop."""
    return {
        "messages": [AIMessage(content=CRISIS_RESPONSE)],
        "booking_step": "none",
        "severity": "crisis",
    }


def scheduler_node(state: AgentState) -> dict:
    """Multi-step booking: ask_intent → wait_intent → ask_slots → wait_slots → broadcast → done."""
    step = state.get("booking_step", "none")
    data = state.get("booking_data") or {}
    last_msg = state["messages"][-1]
    last_content = _get_content_str(getattr(last_msg, "content", None) or str(last_msg))

    user_id = state.get("user_id", "")
    user = store.get_user(user_id)

    if step == "ask_intent":
        msg = "I've noticed this has been bothering you for a while. Would you like to speak with a professional therapist? (Yes/No)"
        return {"booking_step": "wait_intent", "messages": [AIMessage(content=msg)]}

    if step == "wait_intent":
        if "yes" in last_content.lower():
            msg = (
                "Okay. Please tell me when you're available (e.g. 'next Friday after 11 am', 'any time next Tuesday'). "
                "Optionally, you can specify a preferred therapist gender or city (e.g. 'female therapist in Brooklyn')."
            )
            return {"booking_step": "wait_slots", "messages": [AIMessage(content=msg)]}
        msg = "I understand. I'm here whenever you want to talk."
        return {"booking_step": "none", "messages": [AIMessage(content=msg)]}

    if step == "ask_slots":
        msg = (
            "When would you like to have a session? (e.g. 'next Friday after 11 am', 'any time next Tuesday'). "
            "You can also say your preferred therapist gender or city (e.g. 'female therapist in Brooklyn')."
        )
        return {"booking_step": "wait_slots", "messages": [AIMessage(content=msg)]}

    if step == "wait_slots":
        if not user:
            return {"booking_step": "none", "messages": [AIMessage(content="Please log in to book an appointment.")]}
        # Parse timeslot and optional gender/city from last_content (simplified: use whole message as timeslot)
        timeslot = last_content.strip()
        gender_pref = None
        city_pref = None
        # Naive parsing: "female therapist in Brooklyn" -> gender=female, city=Brooklyn
        words = timeslot.lower().split()
        if "female" in words or "woman" in words:
            gender_pref = "female"
        elif "male" in words or "man" in words:
            gender_pref = "male"
        if "in " in timeslot.lower():
            parts = timeslot.lower().split(" in ", 1)
            if len(parts) == 2:
                city_part = parts[1].strip()
                if city_part:
                    city_pref = city_part.split()[0].capitalize()
                    timeslot = parts[0].strip()
        
        if not timeslot:
            timeslot = last_content.strip()
        
        # Use LLM to get strict ISO times
        parsed_times = _parse_datetime_with_llm(timeslot, state["messages"])
        
        data = {
            "timeslot": timeslot,
            "gender_pref": gender_pref,
            "city_pref": city_pref,
            "start_iso": parsed_times.get("start_iso"),
            "end_iso": parsed_times.get("end_iso"),
        }
        request_id = book_appointment(data, user)
        
        msg = (
            "I've sent your availability to matching therapists in your area. "
            "The first therapist who accepts will confirm the appointment, and you'll both get a calendar invite. "
            "You'll see the appointment in your calendar tab when it's confirmed."
        )
        return {
            "booking_step": "done",
            "booking_data": data,
            "messages": [AIMessage(content=msg)],
        }

    return {"booking_step": "none"}


# --- Routing ---

def route_after_triage(state: AgentState) -> Literal["crisis", "scheduler", "end"]:
    """Route to crisis, scheduler, or end (empathetic reply already in state)."""
    # Use pre-calculated severity if available
    severity = state.get("severity")
    
    # Fallback to re-parsing if not in state (e.g. tests or legacy)
    if not severity:
        last_content = ""
        for m in reversed(state.get("messages", [])):
            if hasattr(m, "content") and m.content:
                last_content = _get_content_str(m.content).lower()
                break
        severity = _parse_severity(last_content)
        crisis_words = ["suicide", "kill myself", "end my life"]
        if any(w in last_content for w in crisis_words):
            severity = "crisis"

    if severity == "crisis":
        return "crisis"
    step = state.get("booking_step", "none")
    if step in ("ask_intent", "wait_intent", "ask_slots", "wait_slots"):
        return "scheduler"
    return "end"


def route_after_scheduler(state: AgentState) -> Literal["scheduler", "end"]:
    step = state.get("booking_step", "none")
    if step in ("wait_intent", "wait_slots"):
        return "end"  # Wait for user input in Chainlit
    if step in ("ask_intent", "ask_slots"):
        return "scheduler"
    return "end"


# --- Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("triage", triage_node)
workflow.add_node("crisis", crisis_node)
workflow.add_node("scheduler", scheduler_node)
workflow.set_entry_point("triage")
workflow.add_conditional_edges("triage", route_after_triage, {"crisis": "crisis", "scheduler": "scheduler", "end": END})
workflow.add_edge("crisis", END)
workflow.add_conditional_edges("scheduler", route_after_scheduler, {"scheduler": "scheduler", "end": END})

app_graph = workflow.compile()
