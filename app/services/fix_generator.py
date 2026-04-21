import json
from openai import OpenAI
from app.core.logger import logger

try:
    client = OpenAI()
except Exception:
    client = None

async def generate_fix(issue: str) -> dict:
    """
    Translates textual SEO diagnostics directly into optimized HTML code replacements via independent OpenAI prompts.
    """
    fallback = {
        "issue": issue,
        "current_code": "<!-- Dependency missing or generation timeout -->",
        "fixed_code": "<!-- Check OpenAI connection limits -->",
        "explanation": "Unable to connect to the upstream engine to resolve a specific code replacement string."
    }

    if not client:
        logger.error("OpenAI not initialized returning degraded offline fallback strings.")
        return fallback

    prompt = f"""
    You are an expert SEO web developer diagnosing explicit DOM node hierarchies.
    Provide a robust technical code fix for the following diagnostic issue: "{issue}".
    
    Explicit Instructions:
    1. Provide a realistic standard HTML snippet demonstrating how this issue currently manifests ("current_code").
    2. Provide the optimized structural HTML replacement directly fixing the core heuristics ("fixed_code"). Keep the string beautifully indented and production-ready.
    3. Offer a very brief textual rationale detailing why this fix is relevant to engine spiders ("explanation").
    
    Return STRICT VALID JSON matching exactly this object mapping:
    {{
      "issue": "{issue}",
      "current_code": "<html string>",
      "fixed_code": "<html string>",
      "explanation": "text string"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an automated code fixing engine resolving exact string modifications strictly wrapped inside standardized JSON output types."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        parsed = json.loads(response.choices[0].message.content.strip())
        
        # Enforce boundary checking ensuring empty values don't break strict schema parsers downstream
        for key in ["issue", "current_code", "fixed_code", "explanation"]:
            if key not in parsed:
                parsed[key] = ""
                
        return parsed

    except Exception as e:
        logger.error(f"Failed to generate specific analytical DOM fix safely: {e}")
        return fallback
