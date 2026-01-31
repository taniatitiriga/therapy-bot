# therapy-bot
Agentic AI chatbot for venting with the ability to schedule therapy sessions with a human professional or call a hotline depending on severity.
Uses LangChain, Google Calendar API, Qdrant (vector database),  Chainlit (web interface).

## Description
By assessing the gravity of the discussion, the bot may:
- Reply in an empathetic way: ask more questions about topic (e.g. "How did that make you feel?"), use short answers that mirror the user's message (e.g. "Sounds like you had a hard day."), simulate active listening, ask before giving advice (e.g. "Do you want to vent, or do you want an advice?").
- If problems are recurring and more serious, propose to schedule an appointment with a professional therapist user. The user may decline or accept. If the user hits accept, another prompt asks the user to select timeslots available and optionally select sorting criteria (gender or city of therapist). The user needs to reply with timeslots of availability (e.g. "next friday after 11 am", "any time next tuesday"). Then, the application filters nearby therapists based on gender and city (if custom not set, select user's city) and broadcasts the timeslot and user data to therapist users awaiting an acceptance - retry for all 1h timeslots user selected as available. Match the first therapist that accepts a timeslot. Once the appointment is set with someone, both users get it in google calendar.
- If the case is severe, no more messages are replied to and the user is prompted to a mental health hotline based on location.

