import os
from openai import OpenAI


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant"
        },
        {
            "role": "user",
            "content": "Write a limerick about the Python programming language"
        }
    ]
)

print(response.choices[0].message.content)

# There once was a coder so fine,
# Whose Python skills truly did shine.
# She wrote with great care,
# And variables to share,
# In her scripts, all code did align.
