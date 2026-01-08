import chainlit as cl
from backend.src.graph import app_graph
from langchain_core.messages import HumanMessage

@cl.on_chat_start
async def start():
    # Initialize session state
    cl.user_session.set("history", [])
    cl.user_session.set("user_id", "user_123")
    cl.user_session.set("booking_state", "none")
    
    await cl.Message(content="Hello. I'm here to listen. How was your day?").send()

@cl.on_message
async def main(message: cl.Message):
    user_id = cl.user_session.get("user_id")
    
    # Current state snapshot
    inputs = {
        "messages": [HumanMessage(content=message.content)],
        "user_id": user_id,
        "recurrence_count": 0, # In prod, fetch from persistent DB
        "booking_step": cl.user_session.get("booking_state")
    }

    # Run the Graph
    # stream_mode="values" allows us to see the outputs of nodes
    async for output in app_graph.astream(inputs):
        for key, value in output.items():
            # 'value' contains the state updates from the node
            if "messages" in value:
                last_msg = value["messages"][-1]
                # Only send if it's an AI response (simplification)
                if hasattr(last_msg, "content") and last_msg.content:
                   await cl.Message(content=last_msg.content).send()
            
            # Update session state if booking status changed
            if "booking_step" in value:
                cl.user_session.set("booking_state", value["booking_step"])