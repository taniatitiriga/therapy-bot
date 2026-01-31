"""Therapist matching and appointment booking. MVP: in-memory match + stub Google Calendar."""
import uuid
from typing import List, Optional, Any
from ..models import User
from . import store


def find_therapists(
    user_location: str,
    gender_pref: Optional[str] = None,
    city_pref: Optional[str] = None,
) -> List[User]:
    """Filter nearby therapists by gender and city (or user's city)."""
    location = (city_pref or user_location).strip() or user_location
    return store.list_therapists(location=location, gender=gender_pref)


def broadcast_request(
    client_user: User,
    timeslot_text: str,
    gender_pref: Optional[str] = None,
    city_pref: Optional[str] = None,
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
    appointment = {
        "request_id": request_id,
        "client_user_id": req["client_user_id"],
        "timeslot": req["timeslot"],
        "client_details": req.get("client_details", {}),
    }
    store.confirm_appointment(request_id, therapist_id, appointment)
    _add_to_calendar_stub(appointment, therapist_id)
    return store.get_appointment(request_id)


def _add_to_calendar_stub(appointment: dict, therapist_id: str) -> None:
    """Stub: in production would create Google Calendar events for client and therapist."""
    pass


def book_appointment(booking_data: dict, client_user: User) -> str:
    """Parse booking_data, broadcast to therapists, return request_id."""
    timeslot = booking_data.get("timeslot", "").strip()
    gender_pref = booking_data.get("gender_pref") or None
    city_pref = booking_data.get("city_pref") or None
    return broadcast_request(client_user, timeslot, gender_pref=gender_pref, city_pref=city_pref)
