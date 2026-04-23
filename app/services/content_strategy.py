import json

from app.core.logger import logger
from app.core.openai_client import get_openai_client

def generate_blog_suggestions(scraped_data: dict, ai_keywords: dict) -> dict:
    client = get_openai_client()
    title = scraped_data.get("title", "")
    description = scraped_data.get("description", "")
    headings_dict = scraped_data.get("headings", {})
    headings = " ".join(item for sublist in headings_dict.values() for item in sublist)
    keywords = ", ".join(ai_keywords.get("keywords", []))

    prompt = f"""
    You are an SEO content strategist.
    Based on the website data, suggest:
    1. 3 blog post ideas (titles)
    2. Target audience
    3. Search intent (informational, transactional, etc.)
    4. Brief outline for each blog

    Use only the provided page content and AI-generated keywords.
    Page title: {title}
    Meta description: {description}
    Headings: {headings}
    Target Keywords: {keywords}

    Return JSON only in this exactly matching format:
    {{
      "blog_posts": [
        {{
          "title": "",
          "target_audience": "",
          "search_intent": "",
          "outline": ["Point 1", "Point 2", "Point 3"]
        }}
      ]
    }}
    """

    if not client:
        return {
            "blog_posts": [
                {
                    "title": "Comprehensive Guide to " + (title or "Our Services"),
                    "target_audience": "General Users",
                    "search_intent": "informational",
                    "outline": ["Introduction", "Core Concepts", "Conclusion"]
                }
            ]
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict SEO strategist that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content.strip())
        if "blog_posts" not in parsed:
            raise ValueError("Missing blog_posts field in AI response")
        return parsed

    except Exception:
        logger.exception("Failed to generate blog suggestions.")
        return {
            "blog_posts": [
                {
                    "title": "Comprehensive Guide to " + (title or "Our Services"),
                    "target_audience": "General Users",
                    "search_intent": "informational",
                    "outline": ["Introduction", "Core Concepts", "Conclusion"]
                }
            ]
        }

def generate_guest_post_titles(scraped_data: dict, ai_keywords: dict) -> dict:
    client = get_openai_client()
    title = scraped_data.get("title", "")
    keywords = ", ".join(ai_keywords.get("keywords", []))

    prompt = f"""
    You are an SEO expert.
    Suggest 5 guest post title ideas that can help this website gain backlinks and authority.

    Website Title: {title}
    Target Keywords: {keywords}

    Return JSON only in this format:
    {{
      "guest_post_titles": ["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"]
    }}
    """

    if not client:
        return {
            "guest_post_titles": [
                """The Ultimate Guide to Industry Trends""",
                """5 Strategies for Success in Your Niche""",
                """How to Master Modern Workflows in 2026""",
            ]
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict SEO expert that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.choices[0].message.content.strip())
        if "guest_post_titles" not in parsed:
            raise ValueError("Missing guest_post_titles field in AI response")
        return parsed

    except Exception:
        logger.exception("Failed to generate guest post titles.")
        return {
            "guest_post_titles": [
                """The Ultimate Guide to Industry Trends""",
                """5 Strategies for Success in Your Niche""",
                """How to Master Modern Workflows in 2026""",
            ]
        }
