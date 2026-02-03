import os
import logging
from datetime import datetime
from typing import Optional
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


# Data Models
class EventExtraction(BaseModel):
    """Basic Event Information"""
    description: str = Field(description="Raw description of the event")
    is_calendar_event: bool = Field(description="Whether this text describes a calendar event?")
    confidence_score: float = Field(description="Confidence score, of this being an event, between 0 and 1.")

class EventDetails(BaseModel):
    """Specific Event Details"""
    name: str = Field(description="Name of the event")
    date: str = Field(description="Date and time of the event in ISO 8601 format")
    duration: int = Field(description="Expected duration of the event in minutes")
    participants: list[str] = Field(description="List of participants")

class EventConfirmation(BaseModel):
    """Event Confirmation Message/Text"""
    message: str = Field(description="Natural language confirmation message of the event")
    calendar_link: Optional[str] = Field(description="Generated link to the calendar event, if applicable.")


# Functions
def extract_event_information(user_input: str) -> EventExtraction:
    """
    LLM call to determine if input is a calendar event
    :param user_input: user_input to extract information from
    :return: EventExtraction object
    """

    logging.info("Starting event extraction analysis.")
    logging.debug(f"User input: {user_input}")

    today = datetime.now()
    date_context = f"Today is {today.strftime('%A, %B %d, %Y')}."

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"{date_context}. Analyze if the text describes a calendar event."
            },
            {
                "role": "user",
                "content": f"{user_input}",
            }
        ],
        response_format=EventExtraction
    )

    result = completion.choices[0].message.parsed

    logging.info(f"Extraction complete.\nDescription: {result.description}\nIs calendar event = {result.is_calendar_event}\nConfidence = {result.confidence_score:.2f}")

    return result


def parse_event_details(description: str) -> EventDetails:
    """Extract specific event details"""

    logging.info("Starting event details parsing")

    today = datetime.now()
    date_context = f"Today is {today.strftime('%A, %B %d, %Y')}."

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"{date_context}. Extract detailed event information. When there is relative date references, use this current date as reference."
            },
            {
                "role": "user",
                "content": f"{description}",
            }
        ],
        response_format=EventDetails
    )

    result = completion.choices[0].message.parsed

    logging.info(f"Parsed Event Details:\nName: {result.name}\nDate = {result.date}\nDuration = {result.duration} minutes.")
    logging.info(f"Participants: {', '.join(result.participants)}")

    return result


def generate_confirmation(event_details: EventDetails) -> EventConfirmation:
    """Generates a confirmation message"""

    logging.info("Generating confirmation message.")

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"Generate a natural language confirmation message for the event. Sign off with name; Koochi"
            },
            {
                "role": "user",
                "content": f"{str(event_details.model_dump())}",
            }
        ],
        response_format=EventConfirmation
    )

    result = completion.choices[0].message.parsed

    logging.info(f"Confirmation message generated successfully.")

    return result


# Chaining workflow
def process_calendar_request(user_input: str) -> Optional[EventConfirmation]:
    """Prompt chaining workflow with gate check"""

    logging.info("Starting calendar request processing.")

    initial_extraction = extract_event_information(user_input)
    if (
        not initial_extraction.is_calendar_event or
        initial_extraction.confidence_score < 0.7
    ):
        logging.warning("Gate check failed")

        return None

    logging.info("Gate check passed, proceeding with event processing.")

    event_details = parse_event_details(initial_extraction.description)
    event_confirmation = generate_confirmation(event_details)

    logging.info("Calendar request processing completed successfully.")

    return event_confirmation



# Testing with user's prompt
prompt = "Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob to discuss the project roadmap."

response = process_calendar_request(prompt)
if response:
    print(f"Confirmation: {response.message}")
    if response.calendar_link:
        print(f"Calendar Link: {response.calendar_link}")

else:
    print("This doesn't appear to be a valid calendar request.")



