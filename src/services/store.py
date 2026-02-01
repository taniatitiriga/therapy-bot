"""In-memory store for MVP: users, therapists, pending appointment requests, confirmed appointments."""
from typing import Dict, List, Optional
from ..models import User

_users: Dict[str, User] = {}
# user_id -> list of pending request dicts: { "request_id", "client_user", "timeslot", "client_details" }
_pending_requests: Dict[str, List[dict]] = {}
# request_id -> { "client_user_id", "therapist_user_id", "timeslot", "accepted_by" }
_confirmed_appointments: Dict[str, dict] = {}


def add_user(user: User) -> None:
    _users[user.user_id] = user


def get_user(user_id: str) -> Optional[User]:
    return _users.get(user_id)


def get_user_by_username(username: str) -> Optional[User]:
    for u in _users.values():
        if u.username == username:
            return u
    return None


def list_therapists(location: Optional[str] = None, gender: Optional[str] = None) -> List[User]:
    out = [u for u in _users.values() if u.is_therapist]
    if location:
        out = [u for u in out if location.lower() in (u.location or "").lower()]
    if gender:
        out = [u for u in out if (u.gender or "").lower() == gender.lower()]
    return out


def add_pending_request(therapist_id: str, request: dict) -> None:
    _pending_requests.setdefault(therapist_id, []).append(request)


def get_pending_requests(therapist_id: str) -> List[dict]:
    return _pending_requests.get(therapist_id, [])


def clear_pending_request(therapist_id: str, request_id: str) -> None:
    reqs = _pending_requests.get(therapist_id, [])
    _pending_requests[therapist_id] = [r for r in reqs if r.get("request_id") != request_id]


def clear_pending_request_globally(request_id: str) -> None:
    """Remove this request from every therapist's pending list (e.g. once accepted)."""
    for tid in list(_pending_requests.keys()):
        clear_pending_request(tid, request_id)


def confirm_appointment(request_id: str, therapist_id: str, appointment: dict) -> None:
    _confirmed_appointments[request_id] = {
        **appointment,
        "therapist_user_id": therapist_id,
        "request_id": request_id,
    }


def get_confirmed_for_user(user_id: str) -> List[dict]:
    return [
        a for a in _confirmed_appointments.values()
        if a.get("client_user_id") == user_id or a.get("therapist_user_id") == user_id
    ]


def get_appointment(request_id: str) -> Optional[dict]:
    return _confirmed_appointments.get(request_id)


def seed_demo_users() -> None:
    """Seed a few demo users so the app works out of the box."""
    if _users:
        return
    add_user(User("user_1", "alice", "Alice User", "New York", "rin671628@gmail.com", "female", False))
    add_user(User("user_2", "bob", "Bob User", "Brooklyn", "bob@example.com", "male", False))
    add_user(User("therapist_1", "dr_smith", "Dr. Jane Smith", "New York", "arthur.atogard.business@gmail.com", "female", True))
    add_user(User("therapist_2", "dr_jones", "Dr. John Jones", "Brooklyn", "john@therapy.com", "male", True))
