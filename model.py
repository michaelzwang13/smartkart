from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

prompt = ""

response = client.responses.create(
  model='gpt-5-nano',
  input=prompt
)

print(response.output_text)
