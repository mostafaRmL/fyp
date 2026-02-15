"""Test Groq API connection"""
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key: {api_key[:20]}..." if api_key else "No API key found!")

try:
    client = Groq(api_key=api_key)
    print("✓ Groq client initialized")
    
    # Test simple completion
    print("\nTesting API call...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, I am working!' in JSON format with a 'message' field."}
        ],
        temperature=0.3,
        max_tokens=100,
        response_format={"type": "json_object"}
    )
    
    print("✓ API call successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
