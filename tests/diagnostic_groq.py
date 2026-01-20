"""
DIAGNOSTIC SCRIPT - Check if Groq LLM is actually being called
"""
import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

print("="*80)
print("GROQ LLM DIAGNOSTIC TEST")
print("="*80)

print(f"\n1. Environment Check:")
print(f"   API Key exists: {bool(api_key)}")
print(f"   API Key length: {len(api_key) if api_key else 0}")
print(f"   Model: {model}")

if not api_key:
    print("\n❌ GROQ_API_KEY not found in environment!")
    print("   Add it to .env file:")
    print("   GROQ_API_KEY=gsk_your_key_here")
    exit(1)

print("\n2. Testing Groq API Connection:")
try:
    client = Groq(api_key=api_key)
    print("   ✅ Groq client initialized")
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    exit(1)

print("\n3. Testing Simple Chat:")
try:
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": "Say 'Working' if you can read this"
        }],
        model=model,
        temperature=0.5,
        max_tokens=50
    )
    print(f"   ✅ Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ Chat failed: {e}")
    exit(1)

print("\n4. Testing Complaint Classification (Exact Same Prompt as Your Code):")

# EXACT SAME PROMPT FROM llm_service.py
title = "Classroom projector not working in CSE Block"
description = "The projector in classroom 301 CSE block has been broken for one week. Faculty cannot conduct presentations."

prompt = f"""Analyze this campus complaint and provide a structured response.

Complaint Title: {title}
Complaint Description: {description}

You are analyzing a complaint from an engineering college campus. Carefully categorize based on these rules:

CATEGORY RULES (VERY IMPORTANT):
- "food": Mess, canteen, food quality, hygiene, menu, food timing, dining hall issues
- "infrastructure": Buildings, classrooms, labs, maintenance, AC, fans, lights, electricity, water supply, furniture, equipment, wifi (except hostel wifi), library infrastructure (AC, furniture, space)
- "academic": Classes, exams, faculty, curriculum, library BOOKS/RESOURCES, timetable, course content
- "hostel": Hostel rooms, hostel facilities, hostel mess, hostel rules, roommates, hostel wifi, hostel maintenance
- "transport": College bus, transport timing, vehicle issues, parking, shuttle service
- "other": Everything else not clearly fitting above

PRIORITY RULES:
- "critical": Safety hazards, health emergencies, major infrastructure failure affecting many students, fire/electrical hazards
- "high": Significant disruption to academics or daily life, urgent repairs needed, affecting multiple people or important facilities
- "medium": Moderate issues that need attention but not urgent, affecting individuals or small groups, quality issues
- "low": Minor inconveniences, suggestions, cosmetic issues, low-impact problems

IMPORTANT EXAMPLES:
- "Library AC not working" = INFRASTRUCTURE (not academic)
- "Library books missing" = ACADEMIC (not infrastructure)
- "Mess food quality" = FOOD
- "Hostel wifi slow" = HOSTEL (not infrastructure)
- "Classroom projector broken" = INFRASTRUCTURE
- "Professor teaching method" = ACADEMIC

Provide analysis in the following JSON format ONLY (no other text):
{{
    "priority": "low" | "medium" | "high" | "critical",
    "category": "food" | "infrastructure" | "academic" | "hostel" | "transport" | "other",
    "sentiment": "negative" | "neutral" | "positive",
    "urgency_score": 0-100,
    "impact_level": "individual" | "group" | "campus-wide",
    "summary": "Brief 1-sentence summary of the core issue",
    "key_issues": ["issue1", "issue2", "issue3"],
    "suggested_authority": "Name of the department/authority that should handle this"
}}

Be very careful with categorization. Think step by step about which category fits best."""

try:
    print(f"   Analyzing: '{title}'")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a campus complaint analysis system for an engineering college. Provide structured, accurate JSON responses ONLY. Pay close attention to proper categorization based on the rules provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=model,
        temperature=0.1,
        max_tokens=500,
        response_format={"type": "json_object"}
    )
    
    result_text = response.choices[0].message.content
    result = json.loads(result_text)
    
    print(f"\n   ✅ AI CLASSIFICATION RESULT:")
    print(f"      Category: {result.get('category')}")
    print(f"      Priority: {result.get('priority')}")
    print(f"      Summary: {result.get('summary')}")
    print(f"      Authority: {result.get('suggested_authority')}")
    
    if result.get('category') == 'infrastructure':
        print(f"\n   🎉 SUCCESS! AI correctly classified as INFRASTRUCTURE")
    else:
        print(f"\n   ❌ WRONG! Expected 'infrastructure', got '{result.get('category')}'")
    
    print(f"\n   Full JSON Response:")
    print(f"   {json.dumps(result, indent=2)}")

except json.JSONDecodeError as e:
    print(f"   ❌ JSON parsing failed: {e}")
    print(f"   Raw response: {result_text}")
except Exception as e:
    print(f"   ❌ Classification failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
