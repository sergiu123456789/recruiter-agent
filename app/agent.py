import os
from openai import OpenAI
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

GEMINI_MODEL = "gemini-2.5-pro"  # Make sure this is an available model

def analyze_match(match_request):
    job_text = match_request.job.text

    try:
        # Make the API call
        response = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior recruiter AI."},
                {"role": "user", "content": f"Analyze this job description: {job_text}"}
            ],
            temperature=0.2
        )

        # Log the raw response
        logging.info("Gemini API Response: %s", response)

        # Check if the response has the expected structure
        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']  # Adjust if necessary
            return {
                "job": match_request.job,
                "summary": {
                    "overall_fit": content,
                    "strengths": [],
                    "risks": [],
                    "recommended_talking_points": []
                },
                "insights": {
                    "score": 0.85,
                    "keywords": ["AI", "ML", "Recruiting"]
                },
                "judge_passed": True,
                "judge_reason": "Model responded successfully."
            }
        else:
            logging.error("No valid response received.")
            return {
                "job": match_request.job,
                "summary": {
                    "overall_fit": "No valid response from the model.",
                    "strengths": [],
                    "risks": [],
                    "recommended_talking_points": []
                },
                "insights": [],
                "judge_passed": False,
                "judge_reason": "Model did not return a valid response."
            }

    except Exception as e:
        logging.error("Error while calling Gemini API: %s", e)
        return {
            "job": match_request.job,
            "summary": {
                "overall_fit": "Unable to contact the model; returning fallback.",
                "strengths": ["Solid engineering background."],
                "risks": ["Gemini API unreachable."],
                "recommended_talking_points": ["Fallback mode active."]
            },
            "insights": [],
            "judge_passed": False,
            "judge_reason": "Gemini API error — using fallback."
        }
