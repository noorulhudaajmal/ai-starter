"""
1. LLM decides when external data is needed
2. Python executes the real-world function (tool)
3. LLM formats the final answer into a strict schema (Pydantic)
"""

import os
import json
import requests
from openai import OpenAI
from pydantic import BaseModel, Field


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


class WeatherReport(BaseModel):
    temperature: float = Field(description="The current temperature in Celsius, of the given location.")
    response: str = Field(description="A brief natural language response to the user question.")
    
    
def get_weather(lat: float, lon: float):
    res = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    
    data = res.json()
    return data["current"]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current temperature for provided coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                },
                "required": ["lat", "lon"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that provides weather information."
    },
    {
        "role": "user",
        "content": "What's the current temperature in San Francisco?"
    }
]

# First LLM call: “Should I use a tool?”
completion = client.chat.completions.create(
    model="gpt-5-nano",
    messages=messages,
    tools=tools,
)

response = completion.choices[0].message

print("Response: ", response)

#Response:  ChatCompletionMessage(content='', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_x08z7t28', function=Function(arguments='{"lon":-122.4194,"lat":37.7749}', name='get_weather'), type='function', index=0)])


# function execution
def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)
    
# human in the loop
for tool_call in response.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    tool_call_id = tool_call.id
    
    result = call_function(name, args)
    
    messages.append(response)
    # Feed tool result back to the LLM
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(result)
    })
    

# Second LLM call: structured response
completion_2 = client.beta.chat.completions.parse(
    model="gpt-5-nano",
    messages=messages,
    tools=tools,
    response_format=WeatherReport
)
    
response_2 = completion_2.choices[0].message.parsed
print("Response 2: ", response_2)

print("\n----------------------\n")
print("Temperature: ", response_2.temperature)
print("Response Text: ", response_2.response)

# Response 2:  temperature=55.0 response='the current temperature in San Francisco is 55 F '
# ----------------------

# Temperature:  55.0
# Response Text:  the current temperature in San Francisco is 55 F 