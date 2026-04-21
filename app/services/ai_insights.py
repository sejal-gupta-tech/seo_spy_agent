import json
from openai import OpenAI
from app.core.logger import logger

try:
    client = OpenAI()
except Exception:
    client = None

def get_ai_insights(audit_data: dict) -> dict:
    """
    Translates raw technical metrics returned from Sitewide local arrays directly into structured executive business language.
    """
    fallback = {"insights": []}
    
    if not client:
        logger.warning("OpenAI client not initialized. Returning empty insights block.")
        return fallback

    findings = audit_data.get("findings", [])
    if not findings:
        return fallback

    # Extract priority technical elements ensuring prompt context size isn't bloated on massive sites
    issues_text = "\n\n".join([
        f"Metric: {f.get('metric', 'Unknown')}\n"
        f"Current Status: {f.get('current_value', '')}\n"
        f"Base Technical Impact: {f.get('business_impact', '')}" 
        for f in findings[:6]
    ])

    prompt = f"""
    You are an executive SEO business analyst.
    
    Convert the following raw technical SEO audit issues directly into actionable business-level insights safely digestible by non-technical leadership.
    
    For each issue:
    1. Label the explicit issue.
    2. Assign a business impact tier (High, Medium, Low).
    3. Assign an execution priority tier (High, Medium, Low).
    4. Provide an explanation translating the logic into traffic or revenue loss mechanics.
    5. Provide an actionable recommendation.
    
    Raw Issues:
    {issues_text}
    
    Return STRICT JSON exactly matching:
    {{
      "insights": [
        {{
          "issue": "String",
          "impact": "High/Medium/Low",
          "priority": "High/Medium/Low",
          "explanation": "String",
          "recommendation": "String"
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business SEO analyst producing strict JSON output exclusively."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content.strip())
        
        if "insights" not in parsed:
            logger.error("Missing standard 'insights' list node within OpenAI payload.")
            return fallback

        return parsed

    except Exception as e:
        logger.error(f"Failed to generate AI insights gracefully: {{e}}")
        return fallback
