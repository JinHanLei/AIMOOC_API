from openai import OpenAI

from settings import OPENAI_API_KEY
from settings import OPENAI_BASE_URL

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Write a limerick about python exceptions"}
    ],
    stream=True,
    temperature=0.1,
)

for chunk in completion:
    print(chunk.choices[0].delta.content)
    print("****************")

