"""Chainlit app: login, chat with therapy bot, calendar embed, therapist notifications."""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import chainlit as cl
from langchain_core.messages import HumanMessage

from src.graph import app_graph
from src.services import store
from src.services.calendar import accept_appointment


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Authenticate users with username/password."""
    store.seed_demo_users()
    
    # Demo passwords (in production, use proper hashing!)
    demo_passwords = {
        "alice": "alice123",
        "bob": "bob123",
        "dr_smith": "doctor123",
        "dr_jones": "doctor123",
    }
    
    # Check if username exists and password matches
    if username in demo_passwords and password == demo_passwords[username]:
        user = store.get_user_by_username(username)
        if user:
            return cl.User(
                identifier=user.user_id,
                metadata={
                    "username": user.username,
                    "full_name": user.full_name,
                    "location": user.location,
                    "email": user.email,
                    "gender": user.gender,
                    "is_therapist": user.is_therapist,
                }
            )
    return None


@cl.on_chat_start
async def start():
    """Initialize chat session after login."""
    store.seed_demo_users()
    
    # Get authenticated user
    chainlit_user = cl.user_session.get("user")
    if not chainlit_user:
        await cl.Message(content="Please log in to continue.").send()
        return
    
    # Get user from store
    user_id = chainlit_user.identifier
    user = store.get_user(user_id)
    
    # Set session variables
    cl.user_session.set("history", [])
    cl.user_session.set("booking_state", "none")
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("app_user", user)
    
    # Welcome message
    welcome_msg = f"**Welcome, {user.full_name}!** 👋\n\n"
    
    if user.is_therapist:
        welcome_msg += "You're logged in as a **therapist**. You'll receive appointment requests here.\n\n"
        # Show pending requests
        await cl.Message(content=welcome_msg).send()
        await _send_therapist_pending(user_id)
        await _send_calendar_section(user_id)
    else:
        welcome_msg += "I'm here to listen. How can I help you today?"
        await cl.Message(content=welcome_msg).send()
        await _send_calendar_section(user_id)


async def _send_calendar_section(user_id: str):
    """Show user's confirmed appointments and a link to calendar."""
    appointments = store.get_confirmed_for_user(user_id)
    if not appointments:
        await cl.Message(
            content="📅 **Your appointments**\n\nNo upcoming appointments.",
            author="Calendar"
        ).send()
        return
    lines = ["📅 **Your appointments**\n"]
    for a in appointments:
        lines.append(f"- {a.get('timeslot', '?')} with client/therapist")
    lines.append("\n[Open in Google Calendar](https://calendar.google.com)")
    await cl.Message(content="\n".join(lines), author="Calendar").send()


async def _send_therapist_pending(therapist_id: str):
    """Show pending appointment requests for therapist with Accept/Reject."""
    pending = store.get_pending_requests(therapist_id)
    if not pending:
        return
    for req in pending:
        rid = req.get("request_id", "")
        client = req.get("client_details", {})
        name = client.get("full_name", "Client")
        timeslot = req.get("timeslot", "?")
        actions = [
            cl.Action(name="accept_appt", payload={"request_id": rid}, label="Accept"),
            cl.Action(name="reject_appt", payload={"request_id": rid}, label="Reject"),
        ]
        await cl.Message(
            content=f"**Appointment request** — {name} at {timeslot}",
            author="Notifications",
            actions=actions,
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    content = (message.content or "").strip()
    user_id = cl.user_session.get("user_id")
    user = cl.user_session.get("app_user")

    if not user_id or not user:
        await cl.Message(content="Please log in to continue.").send()
        return

    # Build graph inputs (preserve booking_step from session)
    history = cl.user_session.get("history", [])
    new_message = HumanMessage(content=content)
    history.append(new_message)
    
    inputs = {
        "messages": history,
        "user_id": user_id,
        "recurrence_count": 0,
        "booking_step": cl.user_session.get("booking_state", "none"),
        "booking_data": cl.user_session.get("booking_data") or {},
    }

    # Stream responses from the graph
    try:
        async for output in app_graph.astream(inputs):
            for key, value in output.items():
                if "messages" in value and value["messages"]:
                    for m in value["messages"]:
                        if hasattr(m, "content") and m.content:
                            await cl.Message(content=m.content).send()
                            history.append(m)
                if "booking_step" in value:
                    cl.user_session.set("booking_state", value["booking_step"])
                if "booking_data" in value:
                    cl.user_session.set("booking_data", value["booking_data"])
        cl.user_session.set("history", history)
    except Exception as e:
        await cl.Message(content=f"Sorry, I encountered an error: {str(e)}").send()


@cl.action_callback("accept_appt")
async def on_accept(action: cl.Action):
    """Handle Accept for therapist appointment request."""
    therapist_id = cl.user_session.get("user_id")
    user = cl.user_session.get("app_user")
    if not user or not user.is_therapist:
        await cl.Message(content="Only therapists can accept appointments.").send()
        return
    request_id = (action.payload or {}).get("request_id", "")
    if not request_id:
        return
    result = accept_appointment(therapist_id, request_id)
    if result:
        await cl.Message(content="✅ Appointment confirmed. It's been added to your calendar.").send()
    else:
        await cl.Message(content="This request was already accepted by another therapist.").send()
    await _send_calendar_section(therapist_id)


@cl.action_callback("reject_appt")
async def on_reject(action: cl.Action):
    """Handle Reject for therapist appointment request."""
    therapist_id = cl.user_session.get("user_id")
    user = cl.user_session.get("app_user")
    if not user or not user.is_therapist:
        await cl.Message(content="Only therapists can reject appointments.").send()
        return
    request_id = (action.payload or {}).get("request_id", "")
    if request_id:
        store.clear_pending_request(therapist_id, request_id)
    await cl.Message(content="Request declined.").send()
