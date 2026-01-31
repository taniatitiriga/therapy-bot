"""Qdrant integration for conversation memory and recurrence detection. MVP: in-memory fallback."""
import os
from typing import List

# Optional: real Qdrant client when QDRANT_URL is set
_qdrant = None

def _get_client():
    global _qdrant
    if _qdrant is None and os.getenv("QDRANT_URL"):
        try:
            from qdrant_client import QdrantClient
            _qdrant = QdrantClient(url=os.environ["QDRANT_URL"])
        except Exception:
            pass
    return _qdrant


# In-memory fallback: store recent message summaries per user for recurrence check
_memory: dict[str, list[str]] = {}


def check_recurrence(user_id: str, message: str, limit: int = 10) -> List[str]:
    """Return similar past messages for this user (recurring themes)."""
    client = _get_client()
    if client:
        # Real Qdrant: search by embedding (would need an embedding model in MVP we skip for simplicity)
        return []
    # In-memory: simple keyword overlap for MVP
    past = _memory.get(user_id, [])
    msg_lower = message.lower()
    similar = [p for p in past[-50:] if any(w in p for w in msg_lower.split() if len(w) > 3)]
    return similar[-limit:]


def save_memory(user_id: str, content: str) -> None:
    """Store a conversation turn for recurrence analysis."""
    client = _get_client()
    if client:
        # Would upsert embedding + payload
        return
    _memory.setdefault(user_id, []).append(content[:500])
    _memory[user_id] = _memory[user_id][-100:]
