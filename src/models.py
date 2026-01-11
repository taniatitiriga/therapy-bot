from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    sentiment_score: float
    recurrence_count: int
    booking_step: str  # "none", "time", "criteria", "confirm"
    booking_data: dict # Stores selected time, gender, radius