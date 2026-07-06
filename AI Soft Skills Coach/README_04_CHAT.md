# README 04 — Chat Pipeline: Text Input, Voice Input, AI Response, Voice Output

This is the heart of the application. Everything about how a message goes from your mouth/keyboard → AI → your ears.

---

## The Two Input Modes

### Mode 1: Text Input
User types in the input box and presses Enter or the send button.

### Mode 2: Voice Input
User clicks the mic button, speaks, clicks again to stop. The audio is transcribed by Groq Whisper, then the text is processed exactly like Mode 1.

---

## Text Message Flow (Detailed)

### Browser Side — `src/static/js/chat.js`

```javascript
const sendMessage = async (text) => {
    if (!text || !text.trim()) return;

    // 1. Add user bubble to chat immediately (optimistic UI)
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    chatContainer.insertAdjacentHTML("beforeend", buildUserBubble(text, timeStr));
    scrollToBottom();

    // 2. Clear input, lock the form
    messageInput.value = "";
    lockComposer();          // disables input and send button
    showTypingIndicator();   // shows three bouncing dots

    // 3. Send to server
    const formData = new FormData();
    formData.append("message", text);
    const response = await fetch("/dashboard/message", { method: "POST", body: formData });
    const data = await response.json();

    removeTypingIndicator();

    if (data.success) {
        // 4. Add AI bubble
        chatContainer.insertAdjacentHTML("beforeend",
            buildAiBubble(data.ai_message.text, data.ai_message.time, data.ai_message.audio_url));
        scrollToBottom();

        // 5. Play the AI voice
        playAiAudio(data.ai_message.audio_url);

        // 6. Update the progress bars on the right panel
        updateDashboardStats(data.scores);

        // 7. Update the feedback card (strengths, improvements, grammar fixes)
        updateCoachAnalysis(data);
    }

    unlockComposer();  // re-enable input
};
```

### Server Side — `src/routes/dashboard.py`

```python
@router.post("/dashboard/message")
async def post_message(request, message=Form(None), audio=File(None)):
    user = request.state.current_user

    # STEP 1: Handle voice input (if audio file was uploaded)
    if audio is not None and audio.filename:
        # Save the audio file
        filepath = f"src/static/audio/uploads/user_{uuid.uuid4().hex}.webm"
        with open(filepath, "wb") as f:
            f.write(await audio.read())
        # Transcribe with Groq Whisper
        llm_service = LLMService()
        message_text = await llm_service.transcribe_audio(filepath)
    else:
        message_text = message

    # STEP 2: Get or create active conversation
    async with Sessionlocal() as session:
        conversation = await conv_repo.get_latest_by_user(user.id)
        if not conversation or conversation.status != "in_progress":
            conversation = await conv_repo.create(Conversation(
                user_id=user.id, topic="New Conversation",
                start_time=datetime.now(), status="in_progress"
            ))

        # Auto-rename conversation topic
        if conversation.topic == "New Conversation":
            conversation.topic = message_text[:30] + "..."

        # STEP 3: Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            sender="user",
            message_text=message_text,
            message_type="audio" if audio_url else "text"
        )
        await msg_repo.create(user_msg)

        # STEP 4: Build conversation history for AI context
        all_msgs = await msg_repo.get_by_conversation_id(conversation.id)
        history = [{"role": m.sender, "text": m.message_text} for m in all_msgs[:-1]]
        #                                                         ↑ exclude the one just saved

        # STEP 5: Get AI coaching response
        llm_service = LLMService()
        coach_data = await llm_service.get_coach_response(message_text, history)
        ai_reply = coach_data["response"]

        # STEP 6: Save AI message
        await msg_repo.create(Message(
            conversation_id=conversation.id,
            sender="ai",
            message_text=ai_reply
        ))

        # STEP 7: Convert AI reply to speech
        tts_url = await TTSService.synthesize(ai_reply)

        # STEP 8: Save/update analysis scores
        # (create new Analysis or update existing one for this conversation)

        # STEP 9: Update UserProgress aggregate stats

        # STEP 10: Commit all changes
        await session.commit()

    # STEP 11: Return everything to browser
    return {
        "success": True,
        "user_message": {"text": message_text, "time": "06:52 PM"},
        "ai_message": {"text": ai_reply, "time": "06:52 PM", "audio_url": tts_url},
        "scores": {"overall": 82, "grammar": 85, ...},
        "grammar_suggestions": [...],
        "feedback": "...",
        "strengths": [...],
        "improvements": [...]
    }
```

---

## Voice Recording (Browser Side)

**File:** `src/static/js/chat.js`

### Starting Recording

```javascript
recordButton.addEventListener("click", async () => {
    if (!isRecording) {
        audioChunks = [];

        // 1. Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // 2. Pick best supported audio format
        const preferredMime = [
            "audio/webm;codecs=opus",  // Chrome, Edge (best)
            "audio/webm",              // Chrome fallback
            "audio/ogg;codecs=opus",   // Firefox
            "audio/mp4",               // Safari
        ].find(m => MediaRecorder.isTypeSupported(m)) || "";

        // 3. Create recorder
        mediaRecorder = new MediaRecorder(stream, { mimeType: preferredMime });

        // 4. Collect audio chunks as they come
        mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };

        // 5. When recording stops, combine chunks and send
        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());  // release microphone
            const audioBlob = new Blob(audioChunks, { type: preferredMime });
            await sendAudioMessage(audioBlob);
        };

        mediaRecorder.start(250);   // collect data every 250ms (reliability)
        setRecordingUI(true);       // button turns red, timer starts
    } else {
        // Stop recording — triggers onstop callback above
        mediaRecorder.stop();
        setRecordingUI(false);
        stopTimer();
    }
});
```

### Sending the Audio

```javascript
const sendAudioMessage = async (audioBlob) => {
    lockComposer();
    showTypingIndicator();

    const formData = new FormData();
    // File extension based on actual mime type
    const ext = audioBlob.type.includes("ogg") ? ".ogg" :
                audioBlob.type.includes("mp4") ? ".mp4" : ".webm";
    formData.append("audio", audioBlob, `recording${ext}`);

    const response = await fetch("/dashboard/message", { method: "POST", body: formData });
    const data = await response.json();
    removeTypingIndicator();

    if (data.success) {
        // data.user_message.text is the TRANSCRIBED text
        chatContainer.insertAdjacentHTML("beforeend",
            buildUserBubble(data.user_message.text, data.user_message.time));
        chatContainer.insertAdjacentHTML("beforeend",
            buildAiBubble(data.ai_message.text, data.ai_message.time, data.ai_message.audio_url));
        playAiAudio(data.ai_message.audio_url);
    }
};
```

---

## Voice Transcription (Server Side)

**File:** `src/services/llm_service.py`

```python
async def transcribe_audio(self, filepath: str) -> str:
    load_dotenv(override=True)
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    client = AsyncGroq(api_key=groq_key)
    with open(filepath, "rb") as file:
        transcription = await client.audio.transcriptions.create(
            file=(os.path.basename(filepath), file.read()),
            model="whisper-large-v3",    # OpenAI Whisper model, hosted by Groq
        )
    return transcription.text   # e.g. "Hello, how are you doing today?"
```

**Groq Whisper Large v3** is one of the best speech-to-text models available. It understands accents, handles pauses well, and is very fast because Groq runs it on custom hardware.

---

## AI Voice Response (Text-to-Speech)

**File:** `src/services/tts_service.py`

```python
import edge_tts
import uuid
import os

class TTSService:
    @staticmethod
    async def synthesize(text: str, output_dir: str = "src/static/audio") -> str:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"reply_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(output_dir, filename)

        # Microsoft Edge TTS — free, high quality, no API key needed
        communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
        await communicate.save(filepath)   # saves as MP3

        return f"/static/audio/{filename}"   # web URL
```

**Voice:** `en-US-AvaNeural` — Microsoft's Ava neural voice. It sounds natural and conversational.

**How it works:**
- `edge_tts` library connects to Microsoft's Text-to-Speech service (same one in Microsoft Edge browser)
- No API key needed — it uses the same public endpoint
- Each AI reply generates a new uniquely-named MP3 file
- The file is served directly by FastAPI's static file server

**Note:** Audio files accumulate in `src/static/audio/`. Manual cleanup is needed if the folder gets too large.

---

## Audio Playback (Browser Side)

```javascript
const playAiAudio = (audioUrl) => {
    if (!audioUrl) return;

    // Stop any currently playing audio first
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    const audio = new Audio(audioUrl);
    currentAudio = audio;

    // Visual feedback: mic button turns blue while AI speaks
    if (recordButton) recordButton.classList.add("ai-speaking");

    audio.addEventListener("ended", () => {
        recordButton.classList.remove("ai-speaking");
        currentAudio = null;
    });

    audio.play().catch((e) => {
        // Browser may block autoplay — show a toast instead
        showToast("AI replied. Click the 🔊 button to hear it.");
    });
};
```

**Autoplay Policy:** Modern browsers block audio that plays without user interaction. If the user has not clicked anything on the page yet, autoplay will fail. The code handles this gracefully by showing a toast notification and adding a 🔊 replay button to each AI message bubble.

---

## The Chat Message Bubbles (HTML)

```javascript
// User bubble (right side, purple)
const buildUserBubble = (text, time) => `
    <div class="chat-row user-row fade-in-up">
        <div class="chat-avatar user-avatar"><i class="bi bi-person-circle"></i></div>
        <div class="chat-bubble user-bubble">
            <p class="bubble-text">${escapeHtml(text)}</p>
            <div class="bubble-footer">
                <span class="bubble-time">${time}</span>
                <span class="read-receipt"><i class="bi bi-check2-all"></i></span>
            </div>
        </div>
    </div>`;

// AI bubble (left side, white) with optional 🔊 button
const buildAiBubble = (text, time, audioUrl) => {
    const speakBtn = audioUrl
        ? `<button class="speak-btn" data-audio="${audioUrl}">
               <i class="bi bi-volume-up-fill text-primary"></i>
           </button>`
        : "";
    return `
    <div class="chat-row assistant-row fade-in-up">
        <div class="chat-avatar ai-avatar"><i class="bi bi-robot"></i></div>
        <div class="chat-bubble assistant-bubble">
            <p class="bubble-text">${escapeHtml(text)}</p>
            <div class="bubble-footer">
                <span class="bubble-time">${time}</span>
                ${speakBtn}
            </div>
        </div>
    </div>`;
};
```

**`escapeHtml()`** prevents XSS attacks — if the AI or user sends text with `<script>` tags, they are converted to `&lt;script&gt;` and displayed as text, not executed.

---

## Live Score Updates

After every message, the right panel scores update without page reload:

```javascript
const updateDashboardStats = (scores) => {
    // Update the circular progress ring
    const ring = document.querySelector(".progress-ring");
    ring.dataset.score = scores.overall;
    ring.style.setProperty("--score", String(scores.overall));
    ring.querySelector(".progress-ring-value").textContent = `${scores.overall}%`;

    // Update each metric bar
    const metricMap = {
        "Fluency": scores.fluency,
        "Grammar": scores.grammar,
        "Vocabulary": scores.vocabulary,
        "Pronunciation": scores.pronunciation,
        "Confidence": scores.confidence
    };
    document.querySelectorAll(".metric-item").forEach((item) => {
        const labelText = item.querySelector(".metric-label").textContent.trim();
        for (const [label, val] of Object.entries(metricMap)) {
            if (labelText.includes(label)) {
                item.querySelector(".metric-bar").style.width = `${val}%`;
                item.querySelector("strong").textContent = `${val}%`;
            }
        }
    });
};
```

---

## Keyboard Shortcut

Pressing `M` on the keyboard toggles the microphone (when not typing in the input box):

```javascript
document.addEventListener("keydown", (e) => {
    const tag = document.activeElement?.tagName?.toLowerCase();
    const isEditable = document.activeElement?.isContentEditable;

    // Only trigger if NOT in a text field
    if (tag === "input" || tag === "textarea" || tag === "select" || isEditable) return;

    if (e.key.toLowerCase() === "m" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        recordButton.click();
    }
});
```
