"""Therapist matching and appointment booking. MVP: in-memory match + Google Calendar integration."""
import uuid
from typing import List, Optional, Any
from ..models import User
from . import store
from . import gcal


def find_therapists(
    user_location: str,
    gender_pref: Optional[str] = None,
    city_pref: Optional[str] = None,
) -> List[User]:
    """Filter nearby therapists by gender and city (or user's city)."""
    location = (city_pref or user_location).strip() or user_location
    if location.lower() == "unknown":
        location = ""
    return store.list_therapists(location=location, gender=gender_pref)


def broadcast_request(
    client_user: User,
    timeslot_text: str,
    gender_pref: Optional[str] = None,
    city_pref: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
) -> str:
    """Broadcast appointment request to matching therapists. Returns request_id."""
    therapists = find_therapists(
        client_user.location,
        gender_pref=gender_pref,
        city_pref=city_pref or client_user.location,
    )
    request_id = str(uuid.uuid4())
    request = {
        "request_id": request_id,
        "client_user_id": client_user.user_id,
        "client_details": client_user.to_dict(),
        "timeslot": timeslot_text,
        "start_iso": start_iso,
        "end_iso": end_iso,
    }
    for t in therapists:
        store.add_pending_request(t.user_id, request)
    return request_id


def accept_appointment(therapist_id: str, request_id: str) -> Optional[dict]:
    """First therapist to accept gets the appointment. Returns appointment dict or None."""
    reqs = store.get_pending_requests(therapist_id)
    req = next((r for r in reqs if r.get("request_id") == request_id), None)
    if not req:
        return None
    
    store.clear_pending_request_globally(request_id)
    
    # Enrich appointment with request details
    appointment = {
        "request_id": request_id,
        "client_user_id": req["client_user_id"],
        "timeslot": req["timeslot"],
        "client_details": req.get("client_details", {}),
        "start_iso": req.get("start_iso"),
        "end_iso": req.get("end_iso"),
    }
    
    store.confirm_appointment(request_id, therapist_id, appointment)
    
    # Create real calendar events (separate for client and therapist to have custom titles)
    # We create two events. The link returned to the UI (for the client) will be the client's event link.
    link_client = _create_real_calendar_event(appointment, therapist_id, target="client")
    link_therapist = _create_real_calendar_event(appointment, therapist_id, target="therapist")
    
    if link_client:
        appointment["calendar_link"] = link_client
        # We could store therapist link too if needed, e.g. appointment["therapist_link"] = link_therapist
        # For MVP, storing the client link in the main field ensures the user sees it.
        store.confirm_appointment(request_id, therapist_id, appointment)
        
    return store.get_appointment(request_id)


def _create_real_calendar_event(appointment: dict, therapist_id: str, target: str = "client") -> str:
    """Create Google Calendar event for a specific target (client or therapist)."""
    start_iso = appointment.get("start_iso")
    end_iso = appointment.get("end_iso")
    
    if not start_iso or not end_iso:
        print("Skipping calendar event: missing ISO dates.")
        return ""
        
    therapist = store.get_user(therapist_id)
    client_id = appointment.get("client_user_id")
    client = store.get_user(client_id)
    
    client_name = client.full_name if client else 'Client'
    therapist_name = therapist.full_name if therapist else 'Therapist'
    
    emails = []
    summary = ""
    
    if target == "client":
        summary = f"Therapy Session with {therapist_name}"
        if client and client.email:
            emails.append(client.email)
    else: # target == "therapist"
        summary = f"Therapy Session with {client_name}"
        if therapist and therapist.email:
            emails.append(therapist.email)

    description = f"Therapy session booked via Therapy Bot.\nRequest ID: {appointment['request_id']}"
    
    return gcal.create_event(
        summary=summary,
        start_iso=start_iso,
        end_iso=end_iso,
        attendees_emails=emails,
        description=description
    )


def book_appointment(booking_data: dict, client_user: User) -> str:
    """Parse booking_data, broadcast to therapists, return request_id."""
    timeslot = booking_data.get("timeslot", "").strip()
    gender_pref = booking_data.get("gender_pref") or None
    city_pref = booking_data.get("city_pref") or None
    start_iso = booking_data.get("start_iso")
    end_iso = booking_data.get("end_iso")
    
    return broadcast_request(
        client_user, 
        timeslot, 
        gender_pref=gender_pref, 
        city_pref=city_pref,
        start_iso=start_iso,
        end_iso=end_iso
    )