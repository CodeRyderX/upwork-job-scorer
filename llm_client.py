import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-haiku-4-5"

def score_job(title: str, description: str) -> dict:
    prompt = f"""
You are evaluating a freelance job posting for an automation specialist with these skills in order of strength:
1. n8n
2. GoHighLevel / GHL
3. Make.com
4. Airtable
5. Notion
6. Google Sheets
7. General automation, webhooks, API integrations, workflows
8. Zapier

Job Title: {title}

Job Description: {description}

Score this job from 0 to 100 based on how good a fit it is for this specialist.
Also list which specific skills from the list above are mentioned or implied.
Also give a one sentence reason for the score.

Respond in this exact JSON format:
{{
  "score": 85,
  "keywords_matched": ["n8n", "GoHighLevel"],
  "reason": "Strong n8n and GHL focus with clear automation scope."
}}
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    import json
    return json.loads(content)