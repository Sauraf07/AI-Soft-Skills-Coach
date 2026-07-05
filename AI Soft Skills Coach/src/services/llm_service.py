import os
import json
import httpx
from dotenv import load_dotenv
from typing import Dict, Any, List
from groq import AsyncGroq

SYSTEM_PROMPT = """You are SpeakAI, an expert AI Soft Skills and Communication Coach. Your goal is to help the user improve their spoken and written English, vocabulary, grammar, and overall professional communication.

Analyze the user's message in the context of the conversation history.
Provide:
1. A supportive, conversational response to the user as their coach. Keep the response natural, engaging, and prompting further conversation.
2. Soft skills analysis:
   - scores (out of 100) for grammar, vocabulary, fluency, confidence, pronunciation (default to 80 for text responses), and overall.
   - grammar suggestions: list of corrections with the wrong phrase and the corrected phrase.
   - feedback: brief constructive feedback summary.
   - strengths: 1-2 points of what was good about their input.
   - improvements: 1-2 practical tips for improvement.

Respond strictly in valid JSON format matching this schema:
{
  "response": "Your conversational reply to the user as their coach",
  "scores": {
    "grammar": 85,
    "vocabulary": 80,
    "fluency": 75,
    "confidence": 90,
    "pronunciation": 80,
    "overall": 82
  },
  "grammar_suggestions": [
    {"wrong": "incorrect sentence from user input", "right": "corrected version of the sentence"}
  ],
  "feedback": "summary paragraph of constructive coaching feedback",
  "strengths": ["strength point 1", "strength point 2"],
  "improvements": ["improvement point 1", "improvement point 2"]
}
Do not include any formatting or wrapper outside of the JSON block. Do not include markdown code block syntax (like ```json ... ```)."""

class LLMService:
    def __init__(self):
        # Always reload .env so changes (e.g. via Settings modal) take effect
        # without needing a server restart.
        load_dotenv(override=True)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.groq_api_key   = os.getenv("GROQ_API_KEY",   "").strip() or None

        if self.groq_api_key:
            self.groq_client = AsyncGroq(api_key=self.groq_api_key)
        else:
            self.groq_client = None

    async def get_coach_response(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        # Build context prompt
        history_str = ""
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Coach"
            history_str += f"{role_label}: {msg['text']}\n"
            
        full_prompt = f"{SYSTEM_PROMPT}\n\nConversation History:\n{history_str}\nUser's Message: {message}\n"

        # Try Gemini first if key exists
        if self.gemini_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json"
                        }
                    }
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result_json = response.json()
                    text_content = result_json["candidates"][0]["content"]["parts"][0]["text"]
                    return self._parse_json_response(text_content)
            except Exception as e:
                print(f"Gemini API error: {e}")
                # Fall through to Groq if key exists, otherwise return fallback

        # Try Groq if key exists
        if self.groq_client:
            try:
                chat_completion = await self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Conversation History:\n{history_str}\nUser's Message: {message}"}
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"},
                    timeout=30.0
                )
                text_content = chat_completion.choices[0].message.content
                return self._parse_json_response(text_content)
            except Exception as e:
                err_str = str(e)
                print(f"Groq API error: {err_str}")

                # Detect auth errors and return a helpful, user-friendly response
                if "401" in err_str or "invalid_api_key" in err_str or "Invalid API Key" in err_str:
                    return {
                        "response": "⚠️ Your Groq API key is invalid or expired. Please click ⚙️ Settings in the sidebar, paste a valid key (starting with gsk_), and save. You can get a free key at console.groq.com.",
                        "scores": {"grammar": 0, "vocabulary": 0, "fluency": 0, "confidence": 0, "pronunciation": 0, "overall": 0},
                        "grammar_suggestions": [],
                        "feedback": "API key issue — please update it in Settings.",
                        "strengths": [],
                        "improvements": ["Add a valid GROQ_API_KEY in Settings to enable AI coaching."]
                    }
                # Any other Groq error — surface it cleanly
                return {
                    "response": f"⚠️ The AI coach is temporarily unavailable ({type(e).__name__}). Please try again in a moment.",
                    "scores": {"grammar": 0, "vocabulary": 0, "fluency": 0, "confidence": 0, "pronunciation": 0, "overall": 0},
                    "grammar_suggestions": [],
                    "feedback": "Temporary AI error. Please retry.",
                    "strengths": [],
                    "improvements": ["Try sending your message again."]
                }

        # If no keys are set, return a helpful mock response guiding the user to configure their API key
        return {
            "response": f"I received your message: '{message}'. To unlock full AI-powered coaching and dynamic communication analysis, please configure a GROQ_API_KEY in the Settings menu (gear icon in the sidebar) or in the `.env` file of the project.",
            "scores": {
                "grammar": 80,
                "vocabulary": 75,
                "fluency": 70,
                "confidence": 85,
                "pronunciation": 80,
                "overall": 78
            },
            "grammar_suggestions": [
                {"wrong": "API Key is missing", "right": "Configure GROQ_API_KEY in Settings / .env"}
            ],
            "feedback": "To start receiving real-time soft skills feedback and interactive analysis, please configure a valid GROQ_API_KEY in the Settings modal or update the `.env` file in the project folder.",
            "strengths": ["Backend communication is working perfectly"],
            "improvements": ["Please add your API key to enable AI coaching analysis"]
        }

    async def transcribe_audio(self, filepath: str) -> str:
        # Re-read env in case key was updated via Settings
        load_dotenv(override=True)
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if not groq_key:
            return "[Voice transcription requires a GROQ_API_KEY. Please add it in ⚙️ Settings.]"

        try:
            client = AsyncGroq(api_key=groq_key)
            with open(filepath, "rb") as file:
                transcription = await client.audio.transcriptions.create(
                    file=(os.path.basename(filepath), file.read()),
                    model="whisper-large-v3",
                )
                return transcription.text
        except Exception as e:
            err_str = str(e)
            print(f"Audio transcription error: {err_str}")
            if "401" in err_str or "invalid_api_key" in err_str:
                return "[Invalid Groq API key. Please update it in ⚙️ Settings.]"
            return f"[Could not transcribe audio: {type(e).__name__}. Please try again.]"

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            # Clean possible markdown block markers
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except Exception as e:
            print(f"JSON parsing error: {e}. Text was: {text}")
            # Safe parsing recovery
            return {
                "response": text,
                "scores": {
                    "grammar": 75.0,
                    "vocabulary": 75.0,
                    "fluency": 75.0,
                    "confidence": 75.0,
                    "pronunciation": 75.0,
                    "overall": 75.0
                },
                "grammar_suggestions": [],
                "feedback": "Could not parse detailed score details. Response is in raw format.",
                "strengths": ["Sent message"],
                "improvements": ["Formatting retry"]
            }
