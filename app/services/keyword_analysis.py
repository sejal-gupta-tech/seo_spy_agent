import json
from app.core.logger import logger
from app.core.openai_client import get_openai_client

def generate_relevant_keywords(scraped_data: dict, ai_keywords: list) -> dict:
    """
    Leverages GPT-4o-mini to categorize semantic intent and output targeted SEO keyword arrays.
    Returns a strictly validated structured JSON output.
    """
    fallback_response = {
        "primary_keywords": [],
        "long_tail_keywords": [],
        "keyword_intent": {
            "informational": [],
            "transactional": [],
            "navigational": []
        }
    }
    client = get_openai_client()

    if not client:
        logger.warning("OpenAI client not initialized. Returning empty keyword block.")
        return fallback_response

    title = scraped_data.get("title", "")
    description = scraped_data.get("description", "")
    headings_dict = scraped_data.get("headings", {})
    
    h1_tags = headings_dict.get("h1", [])
    h2_tags = headings_dict.get("h2", [])
    
    h1_text = " | ".join(h1_tags) if h1_tags else "None"
    h2_text = " | ".join(h2_tags) if h2_tags else "None"
    ai_keywords_text = ", ".join(ai_keywords) if ai_keywords else "None"

    prompt = f"""
    You are an SEO keyword expert.

    Based on the following website data, generate:
    1. 10 highly relevant SEO keywords
    2. 5 long-tail keywords
    3. Keyword intent classification (informational, navigational, transactional)

    IMPORTANT:
    - Keep keywords relevant to the page content
    - Avoid generic or unrelated keywords
    - Return ONLY valid JSON

    Website Data:
    Page title: {title}
    Meta description: {description}
    H1 headings: {h1_text}
    H2 headings: {h2_text}
    Existing AI keywords: {ai_keywords_text}

    Format exactly:
    {{
      "primary_keywords": [],
      "long_tail_keywords": [],
      "keyword_intent": {{
        "informational": [],
        "transactional": [],
        "navigational": []
      }}
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict SEO keyword expert that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content.strip()
        parsed_json = json.loads(raw_content)

        if not all(key in parsed_json for key in ["primary_keywords", "long_tail_keywords", "keyword_intent"]):
            logger.error("OpenAI JSON response missing required root intent mapping keys.")
            return fallback_response
            
        return parsed_json

    except Exception:
        logger.exception("Failed to generate structured keywords.")
        return fallback_response
