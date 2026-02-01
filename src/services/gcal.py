"""Google Calendar API service.
Requires 'credentials.json' (OAuth Client ID) in project root.
"""
import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    """Authenticate and return the Google Calendar service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, try full flow
                creds = None
        
        if not creds:
            if not os.path.exists("credentials.json"):
                print("Warning: 'credentials.json' not found. Google Calendar integration disabled.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as e:
        print(f"An error occurred building service: {e}")
        return None


def create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    attendees_emails: list[str],
    description: str = "",
    location: str = "",
) -> str:
    """Create a Google Calendar event. Returns HTML link to event or empty string on failure."""
    service = get_calendar_service()
    if not service:
        return ""

    # Get the primary calendar's time zone
    try:
        calendar = service.calendars().get(calendarId='primary').execute()
        time_zone = calendar.get('timeZone', 'UTC')
    except Exception:
        time_zone = 'UTC'

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_iso,
            "timeZone": time_zone,
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": time_zone,
        },
        "attendees": [{"email": email} for email in attendees_emails],
        "reminders": {
            "useDefault": True,
        },
    }

    try:
        event = service.events().insert(calendarId="primary", body=event).execute()
        return event.get("htmlLink", "")
    except HttpError as e:
        print(f"An error occurred creating event: {e}")
        return ""
