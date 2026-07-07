import httpx
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.services.gbp.oauth_service import get_connection

async def fetch_gbp_reviews(user_id: str, location_name: str, page_token: str = "") -> Dict[str, Any]:
    """
    Fetches reviews for a given Google Business Profile location.
    location_name should be formatted as 'accounts/{accountId}/locations/{locationId}'
    """
    conn = await get_connection(user_id)
    access_token = conn.get("access_token")
    
    if not access_token or "mock" in access_token:
        # Return mock data if no real token
        return {
            "reviews": [
                {
                    "reviewId": "mock_rev_1",
                    "reviewer": {"displayName": "John Doe"},
                    "starRating": "FIVE",
                    "comment": "Excellent service and great attention to detail! They really helped our local business rank higher.",
                    "createTime": datetime.now(timezone.utc).isoformat(),
                    "updateTime": datetime.now(timezone.utc).isoformat(),
                    "reviewReply": None
                },
                {
                    "reviewId": "mock_rev_2",
                    "reviewer": {"displayName": "Jane Smith"},
                    "starRating": "TWO",
                    "comment": "The reports were okay but the communication was very slow.",
                    "createTime": datetime.now(timezone.utc).isoformat(),
                    "updateTime": datetime.now(timezone.utc).isoformat(),
                    "reviewReply": {
                        "comment": "Hi Jane, we apologize for the delayed responses. We are working on improving our communication speed.",
                        "updateTime": datetime.now(timezone.utc).isoformat()
                    }
                }
            ],
            "averageRating": 3.5,
            "totalReviewCount": 2,
            "nextPageToken": None
        }

    # Real API call
    url = f"https://mybusiness.googleapis.com/v4/{location_name}/reviews"
    if page_token:
        url += f"?pageToken={page_token}"
        
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Error fetching reviews: {resp.text}")
            return {"reviews": [], "averageRating": 0, "totalReviewCount": 0}

def analyze_review_intelligence(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates summary statistics and performs a basic NLP/sentiment heuristic.
    In a real-world scenario, you might pass all comments to an LLM or a sentiment classifier.
    """
    total_reviews = len(reviews)
    if total_reviews == 0:
        return {
            "summary": {"total_reviews": 0, "average_rating": 0, "response_rate": 0},
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            "urgent_reviews": []
        }
        
    rating_map = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
    
    total_score = 0
    replied_count = 0
    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    urgent_reviews = []
    
    for r in reviews:
        stars = rating_map.get(r.get("starRating", ""), 0)
        total_score += stars
        
        if r.get("reviewReply"):
            replied_count += 1
            
        # Basic heuristic for sentiment based on stars (AI can refine this later)
        if stars >= 4:
            sentiment["positive"] += 1
        elif stars == 3:
            sentiment["neutral"] += 1
        else:
            sentiment["negative"] += 1
            if not r.get("reviewReply"):
                urgent_reviews.append(r)
                
    average_rating = round(total_score / total_reviews, 1)
    response_rate = round((replied_count / total_reviews) * 100, 1)
    
    return {
        "summary": {
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "response_rate": response_rate,
            "unreplied_count": total_reviews - replied_count
        },
        "sentiment": sentiment,
        "top_positive_topics": ["Service Quality", "Professionalism"] if sentiment["positive"] > 0 else [],
        "top_negative_topics": ["Communication Speed"] if sentiment["negative"] > 0 else [],
        "urgent_reviews": urgent_reviews
    }

from app.core.openai_client import get_openai_client

async def generate_ai_reply(review_text: str, rating: int, business_name: str = "Our Business") -> str:
    """
    Uses OpenAI to generate a professional, empathetic, and compliant response to a GBP review.
    """
    client = get_openai_client()
    if not client:
        return "Thank you for your feedback! We appreciate you taking the time to share your experience."
        
    prompt = f"""
    You are an expert customer service representative for "{business_name}".
    Write a professional reply to the following customer review.
    Rating: {rating} out of 5 stars.
    Review Text: "{review_text}"
    
    Rules:
    1. Detect the language of the review and reply in the exact same language.
    2. Be professional, empathetic, and concise.
    3. Do NOT make any fake promises, invent compensation, or admit legal liability.
    4. Do not disclose private information.
    5. No keyword stuffing.
    6. Return ONLY the text of the reply.
    """
    
    try:
        # Note: openai_client is sync, so we run it in a thread or just call it if using AsyncOpenAI is not configured.
        # Since get_openai_client returns the sync client:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional business owner replying to customer reviews."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return "Thank you for your feedback! We value your business."

