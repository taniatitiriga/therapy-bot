from qdrant_client import QdrantClient

# client = QdrantClient(url="http://localhost:6333")

def save_memory(user_id: str, text: str, vector: list):
    # client.upsert(...)
    pass

def check_recurrence(user_id: str, current_text: str):
    """
    Search vector DB for semantically similar past grievances.
    Returns a list of matches.
    """
    # hits = client.search(...)
    return [] # Return empty for dev