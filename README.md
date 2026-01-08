# therapy-bot
Agentic AI chatbot for venting with the ability to schedule therapy sessions with a human professional or call a hotline depending on severity.
Uses LangChain, Google Calendar API, Qdrant (vector database),  Chainlit (web interface).

## Description
By assessing the gravity of the discussion, the bot may:
- reply in an empathetic way (short answers, ask questions about topic, simulate active listening),
- if problems are recurring and more serious, propose to schedule an appointment with a professional therapist user. the user may decline or accept. if the user hits accept, another prompt asks the user to select timeslots available and, if they wish, select sorting criteria (gender or proximity radius of therapist). After this reply, based on selected criteria, the bot notifies all nearby therapists and tries to wait for the first available slot to be accepted by a therapist user. once the appointment is set with someone, both users get it in google calendar.
- if the case is severe, no more messages are replied to and the user is prompted to a hotline

