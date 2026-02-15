"""Check available Groq models"""
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # List available models
    models = client.models.list()
    
    print("✓ Available Groq Models:\n")
    for model in models.data:
        print(f"  - {model.id}")
        
except Exception as e:
    print(f"✗ Error: {e}")
