# README 05 — AI Integration: Groq, Gemini, Whisper, and the Coaching Prompt

---

## Overview

The AI layer has three components:

| Component | Service | Purpose |
|-----------|---------|---------|
| **Coaching responses** | Groq LLaMA 3.3 70B | Generates all coaching feedback, scores, grammar corrections |
| **Backup AI** | Google Gemini 2.5 Flash | Used if Groq key fails or is missing |
| **Speech-to-Text** | Groq Whisper Large v3 | Transcribes your voice recordings |
| **Text-to-Speech** | Microsoft Edge TTS | Converts AI replies to MP3 voice |

---

## The System Prompt (The Core Instruction)

**File:** `src/services/llm_service.py`

This is the instruction given to the AI before every conversation. It defines who the AI is and exactly what format it must respond in.

```python
SYSTEM_PROMPT = """You are SpeakAI, an expert AI Soft Skills and Communication Coach.
Your goal is to help the user improve their spoken and written English, vocabulary,
grammar, and overall professional communication.

Analyze the user's message in the context of the conversation history.
Provide:
1. A supportive, conversational response to the user as their coach.
   Keep the response natural, engaging, and prompting further conversation.
2. Soft skills analysis:
   - scores (out of 100) for grammar, vocabulary, fluency, confidence,
     pronunciation (default to 80 for text responses), and overall.
   - grammar suggestions: list of corrections with the wrong phrase and corrected phrase.
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
    {"wrong": "incorrect sentence from user", "right": "corrected version"}
  ],
  "feedback": "summary paragraph of constructive coaching feedback",
  "strengths": ["strength point 1", "strength point 2"],
  "improvements": ["improvement point 1", "improvement point 2"]
}
Do not include any formatting outside the JSON. No markdown code blocks."""
```

**Why JSON format?**
The server needs to extract individual fields (scores, feedback, etc.) and return them separately to the browser. By forcing JSON output, we can use `json.loads()` to get a Python dictionary directly.

---

## How the AI is Called

**File:** `src/services/llm_service.py`

```python
async def get_coach_response(self, message: str, history: list) -> dict:
    # Build the history string
    history_str = ""
    for msg in history:
        role_label = "User" if msg["role"] == "user" else "Coach"
        history_str += f"{role_label}: {msg['text']}\n"

    # Full prompt = system instructions + history + new message
    full_prompt = f"{SYSTEM_PROMPT}\n\nConversation History:\n{history_str}\nUser's Message: {message}\n"
```

### Example of what gets sent to the AI:

```
You are SpeakAI... [long system prompt]

Conversation History:
User: Hello, how are you?
Coach: Hi there! I'm doing great. What would you like to work on?
User: I wants to improve my speaking skill.

User's Message: I wants to improve my speaking skill.
```

The AI sees the full conversation and knows to correct "I wants" to "I want".

---

## Provider Priority: Gemini → Groq → Fallback

```python
class LLMService:
    def __init__(self):
        load_dotenv(override=True)   # always re-read .env
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        self.groq_api_key   = os.getenv("GROQ_API_KEY",   "").strip() or None

        if self.groq_api_key:
            self.groq_client = AsyncGroq(api_key=self.groq_api_key)
        else:
            self.groq_client = None
```

### Try 1: Google Gemini

```python
if self.gemini_api_key:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            response = await client.post(url, json=payload)
            response.raise_for_status()
            text_content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(text_content)
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Falls through to Groq
```

### Try 2: Groq LLaMA 3.3 70B

```python
if self.groq_client:
    try:
        chat_completion = await self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Conversation History:\n{history_str}\nUser's Message: {message}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},   # forces JSON output
            timeout=30.0
        )
        text_content = chat_completion.choices[0].message.content
        return self._parse_json_response(text_content)

    except Exception as e:
        # 401 invalid key → friendly message
        if "401" in str(e) or "invalid_api_key" in str(e):
            return {
                "response": "⚠️ Your Groq API key is invalid. Please update it in ⚙️ Settings.",
                "scores": {"grammar": 0, ...},
                ...
            }
        # Other errors → temporary error message
        return {
            "response": "⚠️ AI coach temporarily unavailable. Please try again.",
            ...
        }
```

### Try 3: Fallback (No Keys)

```python
return {
    "response": f"I received your message: '{message}'. Please configure a GROQ_API_KEY in Settings.",
    "scores": {"grammar": 80, "vocabulary": 75, ...},
    ...
}
```

This fallback ensures the app never crashes even without API keys. The user gets a message telling them what to do.

---

## JSON Response Parsing

```python
def _parse_json_response(self, text: str) -> dict:
    try:
        cleaned = text.strip()
        # Remove markdown code blocks if AI added them despite instructions
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except Exception as e:
        # If JSON is malformed, return the raw text as the response
        return {
            "response": text,
            "scores": {"grammar": 75.0, "vocabulary": 75.0, ...},
            "grammar_suggestions": [],
            "feedback": "Could not parse detailed scores.",
            "strengths": ["Sent message"],
            "improvements": ["Formatting retry"]
        }
```

This is defensive — even if the AI returns slightly malformed JSON, the app doesn't crash.

---

## The 6 Scores Explained

| Score | What it measures | For text messages |
|-------|-----------------|-------------------|
| **Grammar** | Correct sentence structure, tense, agreement | Assessed by AI |
| **Vocabulary** | Range and appropriateness of words used | Assessed by AI |
| **Fluency** | Flow and naturalness of expression | Assessed by AI based on text |
| **Confidence** | Assertiveness and directness in tone | Assessed by AI |
| **Pronunciation** | Clarity of speech sounds | Always 80 for text (no audio analysis possible) |
| **Overall** | Weighted average of above | Calculated by AI |

**For voice messages:** Pronunciation can be properly assessed since the AI coach can infer clarity from the transcription quality and how well Whisper could transcribe the audio.

---

## How Scores Are Stored and Displayed

### Storage in `analyses` table:
```python
# First message in a conversation → create new Analysis
analysis = Analysis(
    conversation_id=conversation.id,
    grammar_score=scores.get("grammar", 80),
    vocabulary_score=scores.get("vocabulary", 80),
    ...
)
await analysis_repo.create(analysis)

# Subsequent messages → update the same Analysis row
analysis.grammar_score = scores.get("grammar", 80)
analysis.feedback = feedback_text
await session.flush()
```

### Lifetime average shown in progress ring:
```python
# SQL aggregate query across ALL user conversations
avg_scores = SELECT AVG(grammar_score), AVG(vocabulary_score), ...
             FROM analyses
             JOIN conversations ON analyses.conversation_id = conversations.id
             WHERE conversations.user_id = :user_id
```

The progress ring shows the **average of all time**, not just the current conversation.

---

## Speech-to-Text: Groq Whisper

```python
async def transcribe_audio(self, filepath: str) -> str:
    load_dotenv(override=True)
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    client = AsyncGroq(api_key=groq_key)
    with open(filepath, "rb") as file:
        transcription = await client.audio.transcriptions.create(
            file=(os.path.basename(filepath), file.read()),
            model="whisper-large-v3",
        )
    return transcription.text
```

**Whisper Large v3** details:
- Supports 99+ languages
- Can handle background noise, accents, pauses
- Returns plain text (no timestamps in this usage)
- Hosted by Groq on custom LPU (Language Processing Unit) hardware → very fast

**File handling:**
- Audio saved to: `src/static/audio/uploads/user_abc123.webm`
- Sent to Groq API as binary
- Transcribed text returned
- Original file stays on disk (not deleted — disk management needed manually)

---

## Text-to-Speech: Microsoft Edge TTS

```python
communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
await communicate.save(filepath)
```

**Available voices** (you can change the voice name in `tts_service.py`):
- `en-US-AvaNeural` — female, conversational (current)
- `en-US-GuyNeural` — male, professional
- `en-US-JennyNeural` — female, friendly
- `en-IN-NeerjaNeural` — Indian English female
- `en-GB-SoniaNeural` — British English female

To change the voice, edit `src/services/tts_service.py`:
```python
communicate = edge_tts.Communicate(text, "en-US-GuyNeural")  # change voice here
```

**No API key required.** Edge TTS uses the same free service Microsoft Edge uses in its Read Aloud feature.
