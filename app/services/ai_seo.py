import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI
from app.core.logger import logger

load_dotenv()

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None
    logger.warning("OpenAI client not initialized for ai_seo. Falling back to safe defaults.")


def generate_seo_suggestions(data: dict) -> dict:
    title = data.get("title", "")
    description = data.get("description", "")
    headings = data.get("headings", {})

    headings_text = " ".join(item for sublist in headings.values() for item in sublist)

    prompt = f"""
    You are an SEO strategist.

    Use only the provided page content.

    Page title: {title}
    Meta description: {description}
    Headings: {headings_text}

    Tasks:
    1. Suggest exactly 3 commercially relevant SEO keywords.
    2. Rewrite the meta description in no more than 160 characters.
    3. Suggest an SEO title between 50 and 60 characters.

    Return JSON only in this format:
    {{
        "keywords": ["keyword 1", "keyword 2", "keyword 3"],
        "new_meta_description": "",
        "new_title": ""
    }}
    """

    if not client:
        return {
            "keywords": [],
            "new_meta_description": "",
            "new_title": "",
            "error": "OpenAI client is not configured.",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict SEO strategist that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content.strip())

        if not all(
            key in parsed
            for key in ["keywords", "new_meta_description", "new_title"]
        ):
            raise ValueError("Invalid AI response format")

        return parsed

    except Exception as exc:
        return {
            "keywords": [],
            "new_meta_description": "",
            "new_title": "",
            "error": str(exc),
        }


def extract_main_keyword(ai_result: dict, fallback_text: str = "") -> str:
    keywords = ai_result.get("keywords", [])

    if isinstance(keywords, list):
        for keyword in keywords:
            cleaned_keyword = str(keyword).strip()
            if cleaned_keyword:
                return cleaned_keyword

    fallback_tokens = re.findall(r"[a-z0-9]+", fallback_text.lower())
    return " ".join(fallback_tokens[:5]).strip()
