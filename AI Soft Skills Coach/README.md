# SpeakAI — AI Soft Skills Coach
### Complete Project Documentation

---

## Table of Contents

1. [What is this project?](#1-what-is-this-project)
2. [Technology Stack](#2-technology-stack)
3. [Project Folder Structure](#3-project-folder-structure)
4. [How to Run the Project](#4-how-to-run-the-project)
5. [Environment Variables (.env)](#5-environment-variables-env)
6. [Detailed Documentation Files](#6-detailed-documentation-files)

---

## 1. What is this project?

**SpeakAI** is a web application that acts as your personal AI communication coach.

Think of it like a ChatGPT clone — but instead of just answering questions, it **listens to you speak or reads what you type**, then:
- Replies to you as a **supportive coach** in both text and voice
- **Scores your communication** on Grammar, Vocabulary, Fluency, Confidence, and Pronunciation
- Shows you **grammar mistakes** and how to fix them
- Tracks your **progress over time** across all conversations
- Gives you a full **session report** with homework when you end a conversation
- Rewards you with **achievement badges** as you practice more

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI (Python) | Web server, routes, API |
| **Database** | MySQL | Store all user data |
| **ORM** | SQLAlchemy 2.0 (async) | Python ↔ Database bridge |
| **Migrations** | Alembic | Create/update database tables |
| **AI Model** | Groq (LLaMA 3.3 70B) | Generate coaching responses |
| **AI Backup** | Google Gemini 2.5 Flash | Backup AI if Groq fails |
| **Speech-to-Text** | Groq Whisper Large v3 | Convert your voice to text |
| **Text-to-Speech** | Microsoft Edge TTS | Convert AI reply to voice |
| **Session Auth** | Starlette Sessions + bcrypt | Login/logout/password hashing |
| **Frontend** | Jinja2 Templates + Bootstrap 5 | HTML pages |
| **Frontend JS** | Vanilla JavaScript (Fetch API) | Dynamic chat, mic recording |
| **Async Server** | Uvicorn | Run the FastAPI app |

---

## 3. Project Folder Structure

```
AI Soft Skills Coach/
│
├── main.py                          ← App entry point. Registers everything.
├── requirements.txt                 ← All Python packages needed
├── .env                             ← Secret keys and database URL
├── alembic.ini                      ← Alembic config for migrations
│
├── alembic/                         ← Database migration history
│   ├── env.py                       ← Migration runner
│   └── versions/                    ← One file per database change
│       ├── f630f755f421_user_model_added.py
│       ├── 5705addfbcbc_conversation_model_added.py
│       ├── 7b4012355d2a_message_model_added.py
│       ├── 337dc61bb930_analysis_model_added.py
│       └── ... (13 total migration files)
│
└── src/
    ├── db/
    │   └── db_config.py             ← Database connection setup
    │
    ├── models/                      ← Database table definitions
    │   ├── __init__.py              ← Imports all models together
    │   ├── user.py                  ← User table
    │   ├── conversation.py          ← Conversation table
    │   ├── message.py               ← Messages table
    │   ├── analysis.py              ← AI scores per conversation
    │   ├── user_progress.py         ← Lifetime user stats
    │   ├── learning_goal.py         ← Daily goals
    │   ├── vocabulary_word.py       ← Word of the day
    │   ├── vocabulary_progress.py   ← Word learning status
    │   └── achievement.py           ← Badges earned
    │
    ├── repository/                  ← Database query layer
    │   ├── base_repo.py             ← Generic CRUD operations
    │   ├── user_repo.py             ← User queries
    │   ├── conversation_repo.py     ← Conversation queries
    │   ├── message_repo.py          ← Message queries
    │   ├── analysis_repo.py         ← Analysis queries
    │   └── user_progress_repo.py    ← Progress queries
    │
    ├── services/                    ← Business logic layer
    │   ├── user_service.py          ← Register, login, manage users
    │   ├── conversation_service.py  ← Create/get conversations
    │   ├── dashboard_service.py     ← Build all dashboard data
    │   ├── llm_service.py           ← Talk to Groq/Gemini AI
    │   └── tts_service.py           ← Convert text to speech (MP3)
    │
    ├── routes/                      ← URL handlers (what happens when you visit a URL)
    │   ├── home.py                  ← GET /
    │   ├── auth.py                  ← GET/POST /login, /register, /logout
    │   ├── dashboard.py             ← GET /dashboard, POST /dashboard/message
    │   └── conversation.py          ← GET/POST /conversation, /conversations
    │
    ├── schemas/                     ← Pydantic response shapes (for JSON APIs)
    │   └── conversation.py
    │
    ├── middleware/
    │   └── auth.py                  ← Checks login on every protected page
    │
    ├── exception/
    │   ├── global_exception_handler.py  ← Catches all errors
    │   └── resouce_not_found_exception.py
    │
    ├── utils/
    │   ├── session.py               ← Session helper functions
    │   └── password.py              ← Password hashing with bcrypt
    │
    ├── templates/                   ← HTML pages (Jinja2)
    │   ├── layouts/
    │   │   └── dashboard_base.html  ← Master layout for dashboard pages
    │   ├── partials/
    │   │   ├── sidebar.html         ← Left sidebar component
    │   │   └── topbar.html          ← Top navigation bar
    │   ├── home/
    │   │   └── index.html           ← Landing page
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── register.html
    │   ├── dashboard/
    │   │   ├── chat.html            ← Main chat page
    │   │   └── components/
    │   │       ├── chat_message.html
    │   │       └── ...
    │   └── error.html
    │
    └── static/                      ← CSS, JS, images, audio files
        ├── css/
        │   ├── dashboard.css
        │   ├── dashboard-modern.css
        │   └── chat.css
        ├── js/
        │   ├── chat.js              ← All chat and voice interaction logic
        │   └── dashboard.js         ← Theme toggle, sidebar, ripple effects
        └── audio/
            ├── *.mp3                ← AI voice replies (generated per message)
            └── uploads/             ← User voice recordings (uploaded webm files)
```

---

## 4. How to Run the Project

### Prerequisites
- Python 3.11+
- MySQL running locally on port 3306
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Step 1 — Install dependencies
```bash
cd "AI Soft Skills Coach"
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### Step 2 — Set up the database
Create a MySQL database named `ai_softskill`:
```sql
CREATE DATABASE ai_softskill;
```

### Step 3 — Configure .env
Edit `.env` and set your values:
```env
DATABASE_URL=mysql+aiomysql://root:YOUR_PASSWORD@localhost:3306/ai_softskill
SESSION_SECRET_KEY=any-long-random-string
GROQ_API_KEY=gsk_your_key_here
```

### Step 4 — Run database migrations
```bash
alembic upgrade head
```
This creates all 9 database tables automatically.

### Step 5 — Start the server
```bash
.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6 — Open in browser
Go to: **http://127.0.0.1:8000**

---

## 5. Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | MySQL connection string |
| `SESSION_SECRET_KEY` | Yes | Encrypts the login cookie |
| `GROQ_API_KEY` | Yes | Powers the AI coach (get free at console.groq.com) |
| `GEMINI_API_KEY` | No | Optional backup AI (Google Gemini) |

---

## 6. Detailed Documentation Files

For deep explanations of each layer, read these files in order:

| File | What it covers |
|------|---------------|
| **[README_01_FLOW.md](README_01_FLOW.md)** | Complete request flow from browser to database and back |
| **[README_02_DATABASE.md](README_02_DATABASE.md)** | All 9 database tables, columns, and relationships explained |
| **[README_03_AUTH.md](README_03_AUTH.md)** | Registration, login, sessions, password hashing |
| **[README_04_CHAT.md](README_04_CHAT.md)** | The full chat pipeline: text/voice input → AI → voice output |
| **[README_05_AI.md](README_05_AI.md)** | How the AI works: prompts, scoring, Groq/Gemini integration |
| **[README_06_FRONTEND.md](README_06_FRONTEND.md)** | HTML templates, CSS, JavaScript — how the UI works |
| **[README_07_MIGRATIONS.md](README_07_MIGRATIONS.md)** | Alembic migrations — what each one does |
