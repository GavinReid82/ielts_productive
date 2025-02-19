from openai import OpenAI

import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(model="gpt-4",
messages=[
    {"role": "user", "content": "Hello, can you test if the API is working?"}
])
print(response)