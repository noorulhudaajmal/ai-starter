import os
import logging
from typing import Literal, Optional
from pydantic import BaseModel, Field

from openai import OpenAI


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5-nano"


# Data models
class CalendarRequestType(BaseModel):
    """Determine the type of calendar request"""
    request_type: Literal["new_event", "modify_event"] = Field("Type of calendar request being made.")
    confidence_score: float = Field("Confidence score between 0 and 1.")
    description: str =  Field("Cleaned description of the request.")

class NewEventDetails(BaseModel):
    """Details for creating a new event"""
    name: str = Field("Name of the event")
    date: str = Field("Date of the event in ISO 8601 format")
    duration: int = Field("Duration of the event in minutes")
    participants: list[str] = Field("List of the participants of the event")

class Change(BaseModel):
    """Details for changing an existing event"""
    field: str = Field("Field to change of the existing event")
    new_value: str = Field("New value for the field to change")

class ModifyEventDetails(BaseModel):
    """Details for modifying an existing event"""
    event_identifier : str = Field("Description to identify the existing event")
    changes: list[Change] = Field("List of changes to make")
    participants_to_add: list[str] = Field("List of new participants to add")
    participants_to_remove: list[str] = Field("List of new participants to remove")

class CalendarResponse(BaseModel):
    """Format of the final response for calendar event request"""
    success: bool = Field("Whether or not the calendar request was successful")
    message: str = Field("A user-friendly response message of the calendar request")
    calendar_link: Optional[str] = Field("Link to the calendar request, if applicable")


# Routing and processing functions
def route_calendar_request(user_input: str) -> CalendarRequestType:
    """Route the calendar request to the appropriate type"""

    logging.info("Routing calendar request")

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Determine if this is a request to create a new event or to modify an existing event",
            },
            {
                "role": "user",
                "content": f"{user_input}"
            }
        ],
        response_format=CalendarRequestType
    )

    result = completion.choices[0].message.parsed

    logging.info(f"Request routed as {result.request_type} with a confidence of {result.confidence_score*100: .1f}%")
    return result


def handle_new_event(description: str) -> CalendarResponse:
    """Handle the new event request"""

    logging.info("Processing the new event request")

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Extract the event details for creating a new calendar event",
            },
            {
                "role": "user",
                "content": f"{description}"
            }
        ],
        response_format=NewEventDetails
    )

    details = completion.choices[0].message.parsed

    logging.info(f"New Event details extracted.\n{details.model_dump()}")

    return CalendarResponse(
        success=True,
        message = f"Created a new event '{details.name}' for {details.date} with {', '.join(details.participants)}, expected to be of {details.duration} minutes.",
        calendar_link=f"calendar://new?event={details.name}",
    )

def handle_modify_event(description: str) -> CalendarResponse:
    """Process event modification request"""

    logging.info("Processing the modify event request")

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Extract the event details for modifying an existing calendar event",
            },
            {
                "role": "user",
                "content": f"{description}"
            }
        ],
        response_format=ModifyEventDetails
    )

    details = completion.choices[0].message.parsed

    logging.info(f"Event details extracted.\n{details.model_dump()}")

    return CalendarResponse(
        success=True,
        message=f"Modified event '{details.event_identifier}'",
        calendar_link=f"calendar://modify?event={details.event_identifier}",
    )

def process_calendar_request(user_input: str) -> CalendarResponse:
    """Handles the routing workflow for processing calendar request"""

    logging.info("Processing calendar request")

    route_result = route_calendar_request(user_input)
    if route_result.confidence_score < 0.7:
        logging.info("Low confidence score, not moving forward.")
        return None

    if route_result.request_type == "new_event":
        return handle_new_event(route_result.description)
    elif route_result.request_type == "modify_event":
        return handle_modify_event(route_result.description)
    else:
        logging.info("Unknown calendar request type")
        return None
    return None


# Testing with user's prompt
prompt = "Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob to discuss the project roadmap."

response = process_calendar_request(prompt)
if response:
    print(f"Response: {response.message}")


# 2026-01-25 22:59:06 - INFO - Processing calendar request
# 2026-01-25 22:59:06 - INFO - Routing calendar request
# 2026-01-25 22:59:21 - INFO - HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
# 2026-01-25 22:59:21 - INFO - Request routed as new_event with a confidence of  80.0%
# 2026-01-25 22:59:21 - INFO - Processing the new event request
# 2026-01-25 22:59:32 - INFO - HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
# Response: Created a new event 'New Team Meeting' for Tuesday with Alice, Bob, expected to be of 60 minutes.
# 2026-01-25 22:59:32 - INFO - New Event details extracted.
# {'name': 'New Team Meeting', 'date': 'Tuesday', 'duration': 60, 'participants': ['Alice', 'Bob']}


modify_event_input = (
    "Can you move the team meeting with Alice and Bob to Wednesday at 3pm instead?"
)
result = process_calendar_request(modify_event_input)
if result:
    print(f"Response: {result.message}")

# {'event_identifier': 'unknown', 'changes': [{'field': 'start_time', 'new_value': '13:00'}, {'field': 'attendees', 'new_value': 'Alice,Bob'}], 'participants_to_add': [], 'participants_to_remove': []}

invalid_input = "What's the weather like today?"
result = process_calendar_request(invalid_input)
if not result:
    print("Request not recognized as a calendar operation")

# Request not recognized as a calendar operation
# 2026-01-25 23:02:09 - INFO - Request routed as modify_event with a confidence of  1.0%
# 2026-01-25 23:02:09 - INFO - Low confidence score, not moving forward
