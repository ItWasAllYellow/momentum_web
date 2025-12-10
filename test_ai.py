import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables")
    print("Please copy .env.example to .env and fill in your API key")
    exit(1)

print(f"Testing with key: {API_KEY[:5]}...")
genai.configure(api_key=API_KEY)
try:
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("Hello, are you working?")
    print(f"Success: {response.text}")
except Exception as e:
    print(f"Error: {e}")
