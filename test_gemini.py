# test_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key[:10]}...")

genai.configure(api_key=api_key)

# List available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")

# Try using it
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Say hello")
print(response.text)