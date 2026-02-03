import os
from openai import OpenAI
from pydantic import BaseModel


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# Response format in Pydantic Model
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

# Model call
completion = client.beta.chat.completions.parse(
    model="gpt-5-nano",
    temperature=0,
    messages=[
        {
            "role": "system",
            "content": "Extract the event information"
        },
        {
            "role": "user",
            "content": "Alice and Bob are going to a science fair on Friday."
        }
    ],
    response_format=CalendarEvent
)

event_response = completion.choices[0].message
if event_response.parsed:
    print(event_response.parsed)

    print("---------------------")
    event = event_response.parsed
    print(f"Name: {event.name}")
    print(f"Date: {event.date}")
    print(f"Participants: {event.participants}")

else:
    print(event_response.refusal)

# name='Science Fair' date='Friday' participants=['Alice', 'Bob']
# ---------------------
# Name: Science Fair
# Date: Friday
# Participants: ['Alice', 'Bob']