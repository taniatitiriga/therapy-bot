from typing import TypedDict, List, Optional, Any
from langchain_core.messages import BaseMessage


class User:
    """User account: regular user or therapist."""
    def __init__(
        self,
        user_id: str,
        username: str,
        full_name: str,
        location: str,
        email: str,
        gender: str = "",
        is_therapist: bool = False,
    ):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.location = location
        self.email = email
        self.gender = gender
        self.is_therapist = is_therapist

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "location": self.location,
            "email": self.email,
            "gender": self.gender,
            "is_therapist": self.is_therapist,
        }


class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    user_id: str
    sentiment_score: float
    recurrence_count: int
    booking_step: str  # "none", "ask_intent", "wait_intent", "ask_slots", "wait_slots", "matching", "done"
    booking_data: dict  # timeslots, gender_pref, city_pref, etc.