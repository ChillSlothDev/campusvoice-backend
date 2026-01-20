"""
Quick test to verify Groq API is working - UPDATED FOR 2026
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print(f"API Key found: {bool(api_key)}")
print(f"API Key starts with 'gsk_': {api_key.startswith('gsk_') if api_key else False}")

if not api_key:
    print("❌ GROQ_API_KEY not found!")
    exit(1)

# ✅ USE CURRENT PRODUCTION MODEL (January 2026)
MODEL = "llama-3.3-70b-versatile"

try:
    client = Groq(api_key=api_key)
    
    print(f"\n✅ Testing Groq API with model: {MODEL}...")
    
    # Test 1: Simple response
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say 'API is working. how are you' if you can read this"
            }
        ],
        model=MODEL,
        temperature=0.5,
        max_tokens=50
    )
    
    print(f"✅ API Response: {response.choices[0].message.content}")
    
    # Test 2: JSON response (for complaint analysis)
    print("\n✅ Testing JSON structured output...")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a complaint categorizer. Respond ONLY with valid JSON."
            },
            {
                "role": "user",
                "content": 'Categorize this complaint: "Library AC not working". Return JSON with fields: category, priority, summary'
            }
        ],
        model=MODEL,
        temperature=0.1,
        max_tokens=200,
        response_format={"type": "json_object"}
    )
    
    import json
    result = json.loads(response.choices[0].message.content)
    print(f"✅ JSON Response: {json.dumps(result, indent=2)}")
    print("\n✅ Groq API is working correctly!")
    
except Exception as e:
    print(f"❌ Groq API Error: {e}")
    exit(1)
