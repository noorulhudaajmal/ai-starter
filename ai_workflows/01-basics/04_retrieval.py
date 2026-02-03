import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Defining knowledge base
def search_kb(question: str):
    """Load the whole knowledge base from the JSON file."""
    with open("data/kb.json", "r") as f:
        return json.load(f)


# defining search_kb tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Get the answer to the user's question from the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that answers questions from the knowledge base about our e-commerce store."
    },
    {
        "role": "user",
        "content": "What is the return policy?"
    }

]

completion = client.chat.completions.create(
    model="gpt-5-nano",
    messages=messages,
    tools=tools
)

print(completion.choices[0].message)
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_RNNWTpskLTp21OdIgSOwz9wA', function=Function(arguments='{"question":"What is the return policy?"}', name='search_kb'), type='function')])

def call_function(func_name, args):
    if func_name == "search_kb":
        return search_kb(**args)
    return None


for tool_call in completion.choices[0].message.tool_calls:
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    tool_call_id = tool_call.id

    func_result = call_function(name, arguments)

    messages.append(completion.choices[0].message)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(func_result),
        }
    )


class KBResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question.")
    source: int = Field(description="The reference id of the answer.")


completion_2 = client.chat.completions.parse(
    model="gpt-5-nano",
    messages=messages,
    tools=tools,
    response_format=KBResponse,
)

response = completion_2.choices[0].message.parsed

print(f"Response: {response}")
# Response: answer='Items can be returned within 30 days of purchase with original receipt. Refunds will be processed to the original payment method within 5-7 business days.' source=1

print(f"Answer: {response.answer}")
print(f"Source: {response.source}")
# Answer: Items can be returned within 30 days of purchase with original receipt. Refunds will be processed to the original payment method within 5-7 business days.
# Source: 1


messages = [
    {"role": "system", "content": "You are a helpful assistant that answers questions from the knowledge base about our e-commerce store."},
    {"role": "user", "content": "What is the weather in Tokyo?"},
]

completion_3 = client.beta.chat.completions.parse(
    model="gpt-5-nano",
    messages=messages,
    tools=tools,
)

print(completion_3.choices[0].message.content)
# I don’t have live weather data in this chat, so I can’t provide the current conditions in Tokyo.
#
# If you’re asking about shopping-related stuff for Tokyo, I can help with:
# - Shipping options and estimated delivery times to Tokyo, Japan
# - International shipping rates for a specific item
# - Availability of products for Japan
#
# What would you like me to assist with? If you just need the current weather, please check a weather service like Weather.com, a weather app, or your preferred forecast site.
