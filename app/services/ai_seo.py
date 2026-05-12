import json
import re

from app.core.logger import logger
from app.core.openai_client import get_openai_client


def generate_seo_suggestions(data: dict) -> dict:
    client = get_openai_client()
    title = data.get("title", "")
    description = data.get("description", "")
    headings = data.get("headings", {})
    
    logger.info("Generating SEO suggestions for page title: %s", title[:80])

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
            model="gpt-5.5",
            messages=[
                {"role": "system", "content": "You are a strict SEO strategist that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content.strip())
        logger.debug("SEO suggestions AI response: %s", {"keywords": parsed.get("keywords"), "new_title": parsed.get("new_title")})

        if not all(
            key in parsed
            for key in ["keywords", "new_meta_description", "new_title"]
        ):
            raise ValueError("Invalid AI response format")

        return parsed

    except Exception as exc:
        logger.exception("Failed to generate SEO suggestions.")
        return {
            "keywords": [],
            "new_meta_description": "",
            "new_title": "",
            "error": str(exc),
        }


def generate_consolidated_strategy(primary_page: dict) -> dict:
    """A high-performance unified LLM call that returns keyword strategy, blog themes, and guest posts in one pass."""
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI client not configured for consolidated strategy generation.")
        return {"primary": {}, "blog_posts": [], "guest_post_titles": []}

    title = primary_page.get("title", "")
    desc = primary_page.get("description", "")
    logger.info("Generating consolidated strategy for page: %s", title[:80])
    
    prompt = f"""
    You are an SEO Director. Perform a comprehensive content strategy for this page:
    Title: {title}
    Description: {desc}

    Return a JSON object containing:
    1. "primary": {{ "keywords": [3 words], "new_title": "50-60 chars", "new_meta_description": "140-160 chars" }}
    2. "blog_posts": [2 highly relevant SEO blog post ideas with title and 2-point outline]
    3. "guest_post_titles": [3 authority guest post title ideas]

    Format: JSON only.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5.5",
            messages=[
                {"role": "system", "content": "You are a professional SEO analyst. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content.strip())
        logger.debug("Consolidated AI strategy response keys: %s", list(parsed.keys()))
        return parsed
    except Exception as e:
        logger.error(f"Consolidated AI call failed: {e}")
        return {"primary": {}, "blog_posts": [], "guest_post_titles": []}


def extract_main_keyword(ai_result: dict, fallback_text: str = "") -> str:
    keywords = ai_result.get("keywords", [])
    logger.debug("Extracting main keyword from AI result: %s", keywords)

    if isinstance(keywords, list):
        for keyword in keywords:
            cleaned_keyword = str(keyword).strip()
            if cleaned_keyword:
                logger.info("Main keyword extracted: %s", cleaned_keyword)
                return cleaned_keyword

    fallback_tokens = re.findall(r"[a-z0-9]+", fallback_text.lower())
    return " ".join(fallback_tokens[:5]).strip()
