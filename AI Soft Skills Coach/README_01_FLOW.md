# README 01 — Complete Request Flow

This document explains exactly what happens, step by step, from the moment a user opens the browser to the moment they see an AI response with voice playback.

---

## The Big Picture

```
Browser
  │
  │  HTTP Request
  ▼
main.py  (FastAPI app)
  │
  ├── Middleware: Auth checks login
  │
  ├── Router: picks the right handler function
  │
  ├── Service: runs business logic
  │
  ├── Repository: queries the database
  │
  ├── External API: calls Groq AI / Edge TTS
  │
  └── Returns HTML page or JSON response back to browser
```

---

## Flow 1 — First Visit (Landing Page)

**URL:** `GET /`

**File:** `src/routes/home.py`

```python
@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home/index.html")
```

**What happens:**
1. Browser requests `http://127.0.0.1:8000/`
2. `Auth` middleware sees `/` is a public URL — skips login check
3. `home.py` renders `src/templates/home/index.html`
4. HTML page is sent to the browser

---

## Flow 2 — Registration

**URL:** `GET /register` then `POST /register`

**File:** `src/routes/auth.py`

```python
@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    native_language: str = Form(...),
):
    async with Sessionlocal() as session:
        user_service = UserService(session)
        user = User(username=username, email=email, password=password, ...)
        user = await user_service.register_user(user)
    return RedirectResponse(url=f"/login?message=...", status_code=303)
```

**Step by step:**
1. User fills the form and clicks Register
2. Browser sends `POST /register` with form data
3. `UserService.register_user()` is called:
   - Checks if email already exists in database
   - If yes → raises `ValueError("email already exists")`
   - If no → hashes the password using bcrypt
   - Saves the new User row to database
   - Creates a blank `UserProgress` row for that user
   - Commits everything to database
4. Redirects to `/login` with success message

**File:** `src/services/user_service.py`
```python
async def register_user(self, user: User):
    existing_user = await self.user_repo.get_user_by_email(user.email)
    if existing_user is not None:
        raise ValueError("An account with this email already exists.")
    user.password = hash_password(user.password)  # bcrypt hash
    created_user = await self.user_repo.create_user(user)
    await self.user_progress_repo.ensure_default_for_user(created_user.id)
    await self.session.commit()
    return created_user
```

**Password hashing** — `src/utils/password.py`:
```python
def hash_password(password: str):
    password_bytes = password.encode('utf-8')
    salt_key = bcrypt.gensalt(12)   # generates random salt
    return bcrypt.hashpw(password_bytes, salt_key).decode('utf-8')
```
The password `"hello123"` becomes something like `"$2b$12$abc...xyz"` — it can NEVER be reversed back to the original.

---

## Flow 3 — Login

**URL:** `POST /login`

**File:** `src/routes/auth.py`

```python
@router.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    async with Sessionlocal() as session:
        user_service = UserService(session)
        user = await user_service.authenticate_user(email=email, password=password)
        if not user:
            return login page with error
        start_user_session(request.session, user)
        return RedirectResponse(url="/dashboard", status_code=303)
```

**`authenticate_user` in UserService:**
```python
async def authenticate_user(self, email: str, password: str):
    user = await self.user_repo.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.password):  # bcrypt compare
        return None
    return user
```

**`start_user_session` in utils/session.py:**
```python
def start_user_session(session: dict, user: User):
    session["is_logged_in"] = True
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.username
```
This stores the user's ID in an **encrypted cookie** on the browser. Every future request sends this cookie automatically.

---

## Flow 4 — Auth Middleware (Every Protected Page)

**File:** `src/middleware/auth.py`

This runs on **every single request** before it reaches any route handler.

```python
class Auth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_urls = {"/", "/login", "/register", "/logout", "/docs", ...}

        # Skip auth for public pages and static files
        if request.url.path.startswith("/static") or request.url.path in public_urls:
            return await call_next(request)

        # Check if logged in
        if not request.session.get("is_logged_in"):
            return RedirectResponse("/login", status_code=303)

        # Load user from database and attach to request
        user_id = request.session.get("user_id")
        async with Sessionlocal() as session:
            user_service = UserService(session)
            current_user = await user_service.get_user_by_id(user_id)

        if current_user is None:
            return RedirectResponse("/login", status_code=303)

        request.state.current_user = current_user  # ← available in all route handlers
        return await call_next(request)
```

After this middleware runs, every route can access the logged-in user via:
```python
user = getattr(request.state, "current_user", None)
```

---

## Flow 5 — Dashboard Page Load

**URL:** `GET /dashboard`

**File:** `src/routes/dashboard.py`

```python
@router.get("/dashboard")
async def dashboard_page(request: Request):
    async with Sessionlocal() as session:
        dashboard_service = DashboardService(session)
        dashboard_context = await dashboard_service.build_context(
            getattr(request.state, "current_user", None)
        )
    return templates.TemplateResponse(
        request=request,
        name="dashboard/chat.html",
        context=dashboard_context,
    )
```

**`DashboardService.build_context()`** in `src/services/dashboard_service.py` does ALL of this in one call:

1. **Daily Goal** — Looks for an active `LearningGoal` for today. If none, creates one ("Practice Speaking — 10 minutes"). Counts user messages sent today to estimate minutes spoken.

2. **Vocabulary Card** — Gets the newest `VocabularyWord` for this user. If none, creates a default one ("Enthusiastic").

3. **Weak Areas** — Reads the last 3 `Analysis` records, extracts the `improvements` field to show what the user needs to work on.

4. **Achievement Badges** — Counts total conversations. Awards badges automatically:
   - 🏅 First Talk — 1 conversation
   - 🚀 Speech Explorer — 5 conversations
   - 🏆 Communication Master — 10 conversations

5. **Average Scores** — SQL aggregate query: `AVG(grammar_score)`, `AVG(vocabulary_score)`, etc., across all user conversations.

6. **Active Conversation** — Gets the most recent in-progress conversation and loads its messages.

7. **Profile** — Builds a profile dict with name, initials, skill level (Beginner/Intermediate/Advanced based on average score).

The returned `dashboard_context` dict is passed to the Jinja2 template as variables.

---

## Flow 6 — Sending a Text Message (The Core Flow)

**URL:** `POST /dashboard/message`

**File:** `src/routes/dashboard.py`

This is the most important flow. Here is every step:

```
User types "Hello, how are you?" and presses Enter
         ↓
chat.js sends: POST /dashboard/message  { message: "Hello, how are you?" }
         ↓
STEP 1: Get or create active Conversation
         ↓
STEP 2: Save user Message to database
         ↓
STEP 3: Fetch full conversation history from database
         ↓
STEP 4: Send history + new message to Groq AI
         ↓
STEP 5: Parse AI JSON response (scores, feedback, reply text)
         ↓
STEP 6: Save AI Message to database
         ↓
STEP 7: Send AI reply text to Edge TTS → get MP3 file path
         ↓
STEP 8: Save/Update Analysis record with new scores
         ↓
STEP 9: Update UserProgress stats (total convs, avg score, minutes)
         ↓
STEP 10: Commit everything to database
         ↓
STEP 11: Return JSON to browser with all data
         ↓
chat.js: Adds both bubbles to chat, plays MP3 audio, updates progress bars
```

### Step 1 — Conversation Management
```python
conversation = await conv_repo.get_latest_by_user(user.id)
if not conversation or conversation.status != "in_progress":
    # Create a new conversation
    conversation = Conversation(
        user_id=user.id,
        topic="New Conversation",
        start_time=datetime.now(),
        status="in_progress"
    )
    conversation = await conv_repo.create(conversation)

# Auto-rename from "New Conversation" to first 30 chars of message
if conversation.topic == "New Conversation":
    conversation.topic = message_text[:30] + "..."
```

### Step 2 — Save User Message
```python
user_msg = Message(
    conversation_id=conversation.id,
    sender="user",
    message_text=message_text,
    message_type="text"  # or "audio" if voice was used
)
await msg_repo.create(user_msg)
```

### Step 3 — Build History for AI
```python
db_messages = await msg_repo.get_by_conversation_id(conversation.id)
history = []
for m in db_messages[:-1]:   # all messages except the one just saved
    history.append({"role": m.sender, "text": m.message_text})
# result: [{"role": "user", "text": "hi"}, {"role": "ai", "text": "hello..."}]
```

### Steps 4-5 — AI Call
See `README_05_AI.md` for full details.

### Step 7 — Text-to-Speech
```python
tts_url = await TTSService.synthesize(ai_reply)
# Returns: "/static/audio/reply_abc123def456.mp3"
```

### Step 11 — JSON Response to Browser
```python
return {
    "success": True,
    "user_message": {"text": "Hello, how are you?", "time": "06:52 PM", "audio_url": None},
    "ai_message": {"text": "Hi there! I'm doing great...", "time": "06:52 PM", "audio_url": "/static/audio/reply_xxx.mp3"},
    "scores": {"overall": 82, "grammar": 85, "vocabulary": 80, "fluency": 75, ...},
    "grammar_suggestions": [{"wrong": "...", "right": "..."}],
    "feedback": "Great communication!",
    "strengths": ["Clear greeting", "Good tone"],
    "improvements": ["Try more complex sentences"]
}
```

---

## Flow 7 — Sending a Voice Message

**Additional steps before Step 1:**

```
User clicks mic button → browser starts MediaRecorder
User speaks → browser captures audio chunks
User clicks mic again → recording stops
         ↓
chat.js sends: POST /dashboard/message  { audio: Blob(webm) }
         ↓
Server saves .webm file to: src/static/audio/uploads/user_uuid.webm
         ↓
LLMService.transcribe_audio(filepath) is called:
  → Reads the audio file
  → Sends to Groq Whisper Large v3 API
  → Returns transcribed text: "Hello, how are you?"
         ↓
Continues with exactly the same flow as text message (Step 1 onwards)
```

---

## Flow 8 — Ending a Session

**URL:** `POST /conversation/{id}/complete`

**File:** `src/routes/conversation.py`

```python
conv.status = "completed"
conv.end_time = datetime.now()
delta = conv.end_time - conv.start_time
conv.duration_seconds = max(60, int(delta.total_seconds()))
await db.commit()
```

Then it returns a full report:
```python
return {
    "report": {
        "topic": "Hello, how are you?...",
        "duration_minutes": 5.2,
        "total_messages": 8,
        "overall_score": 82,
        "metrics": {"grammar": 85, "vocabulary": 80, ...},
        "mistakes": ["Try more complex sentences"],
        "homework": "Write 5 sentences using 'complex sentences' practice..."
    }
}
```

The browser shows this in a modal popup with all scores, mistakes, and a homework assignment.

---

## Flow 9 — Loading a Past Conversation

**URL:** `GET /conversation/{id}` (with `Accept: application/json` header from JS)

```python
@router.get("/conversation/{conversation_id}")
async def get_conversation_page_or_data(...):
    is_json_request = "application/json" in request.headers.get("accept", "")

    conversation_data = await conv_service.get_conversation(conversation_id, user.id)

    if is_json_request:
        return conversation_data   # JSON for JS to render
    else:
        # Full page render for direct URL access
        return templates.TemplateResponse("dashboard/chat.html", context)
```

`ConversationService.get_conversation()` returns:
```python
{
    "conversation": {"id": 5, "topic": "Mock interview...", "status": "completed"},
    "messages": [
        {"sender": "USER", "message": "Let me introduce myself...", "created_at": "..."},
        {"sender": "AI",   "message": "Great introduction!", "created_at": "..."},
        ...
    ]
}
```

JavaScript then renders each message as a chat bubble.

---

## Flow 10 — Logout

**URL:** `GET /logout`

```python
@router.get("/logout")
async def logout(request: Request):
    clear_user_session(request.session)  # removes all session keys
    return RedirectResponse(url="/login", status_code=303)
```

The cookie is wiped. Next request to any protected page → redirected to `/login`.
