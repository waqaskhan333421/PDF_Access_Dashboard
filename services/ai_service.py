import logging
import json
from google import genai
from config import GEMINI_API_KEY

# Configure Gemini Client
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        # Use the modern google-genai library
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        client = None
else:
    client = None

logger = logging.getLogger(__name__)

def analyze_application(application_text: str):
    """
    Analyze user application using the new google-genai package.
    Returns: {score: int, recommendation: str, analysis: str}
    """
    
    # Fallback to keyword system if client is not configured
    if not client:
        return _fallback_keyword_analysis(application_text)

    prompt = f"""
    You are an AI assistant for a secure document management system. 
    Analyze the following user application for access to a PDF document.
    Provide a score from 0 to 100 based on the professional intent, clarity, and legitimacy.
    Also provide a short 1-sentence analysis.
    
    Application Text: "{application_text}"
    
    Respond STRICTLY in the following JSON format:
    {{
        "score": (integer 0-100),
        "recommendation": ("approve", "reject", "review"),
        "analysis": "1-sentence summary"
    }}
    
    Guidelines:
    - 75-100: Academic/professional purpose with detail.
    - 40-74: Legitimate but brief or generic.
    - 0-39: Short, nonsensical, or suspicious.
    """

    try:
        # Use Client.models.generate_content
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        content = response.text.strip()
        # Clean markdown code blocks if AI returns them
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        result = json.loads(content)
        
        # Ensure result has correct structure
        return {
            "score": int(result.get("score", 0)),
            "recommendation": result.get("recommendation", "review").lower(),
            "analysis": result.get("analysis", "No analysis provided.")
        }

    except Exception as e:
        logger.error(f"GenAI analysis failed: {e}")
        return _fallback_keyword_analysis(application_text)


def _fallback_keyword_analysis(text: str):
    """Local rule-based analysis as a fallback."""
    text_lower = text.lower()
    score = 0
    words = text.split()

    keywords = {
        "research": 15, "academic": 15, "thesis": 15, "project": 10, "study": 10,
        "assignment": 10, "evaluation": 10, "learn": 5, "knowledge": 5, "interest": 5, "read": 5,
    }
    
    for word, points in keywords.items():
        if word in text_lower: score += points
            
    if len(words) > 50: score += 20
    elif len(words) > 20: score += 10
    elif len(words) > 5: score += 5
        
    score = min(score, 100)
    
    if score >= 70: recommendation = "approve"
    elif score >= 40: recommendation = "review"
    else: recommendation = "reject"
        
    return {
        "score": score,
        "recommendation": recommendation,
        "analysis": "Analyzed using local keyword engine (Gemini API key not configured or failed)."
    }
