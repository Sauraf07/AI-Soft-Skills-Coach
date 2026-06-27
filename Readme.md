# 🚀 AI Soft Skills Coach

> An AI-powered platform that helps students improve their communication, interview skills, grammar, vocabulary, and confidence through personalized feedback.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-yellow)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-lightgrey)
![AI Powered](https://img.shields.io/badge/AI-Powered-purple)
![License](https://img.shields.io/badge/License-MIT-blue)

---

# 📖 About

AI Soft Skills Coach is an intelligent learning platform designed to help students become interview-ready by improving their communication and professional skills.

Instead of simply chatting with an AI, the application analyzes user responses, provides personalized feedback, tracks improvement over time, and recommends daily exercises based on individual weaknesses.

The project combines modern backend development with AI to create a practical learning experience.

---

# ✨ Features

## 👤 User Management

* User Registration
* Secure Login
* JWT Authentication
* Password Hashing
* User Profile

---

## 💬 Communication Coach

Practice explaining technical concepts.

Example:

> Explain Object-Oriented Programming.

AI evaluates:

* Clarity
* Grammar
* Vocabulary
* Confidence
* Professionalism
* Overall Score

---

## 🎯 Mock Interview

Practice HR and technical interviews.

Features:

* AI-generated questions
* Personalized feedback
* Interview scoring
* Performance history

---

## ✍️ Grammar Assistant

Improve written English.

* Grammar correction
* Sentence improvement
* Writing suggestions
* Explanation of mistakes

---

## 📚 Vocabulary Builder

Daily vocabulary practice.

Includes:

* Word of the day
* Meanings
* Examples
* Synonyms
* Mini quizzes
* Progress tracking

---

## 🎤 Public Speaking Coach

Generate structured speeches.

AI provides:

* Introduction
* Body
* Conclusion
* Speaking tips

---

## 📈 Progress Dashboard

Track learning over time.

Metrics include:

* Communication Score
* Grammar Score
* Vocabulary Score
* Confidence Score
* Interview Score
* Overall Progress

---

## 🧠 AI Personalized Feedback

The AI remembers previous practice sessions and provides personalized suggestions for improvement.

Example:

> "Your grammar has improved by 15% since last week. Focus next on confidence and answer structure."

---

# 🛠 Tech Stack

## Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* MySQL

## Frontend

* Jinja2
* HTML
* CSS
* JavaScript

## AI

* Groq API / Google Gemini API

## Authentication

* JWT
* Passlib
* OAuth2

---

# 📂 Project Structure

```text
AI-SoftSkills-Coach/

│
├── app/
│
├── api/
│   ├── auth.py
│   ├── communication.py
│   ├── interview.py
│   ├── grammar.py
│   ├── vocabulary.py
│   ├── dashboard.py
│
├── models/
│
├── schemas/
│
├── services/
│   ├── ai_service.py
│   ├── scoring.py
│   ├── prompt_service.py
│
├── database/
│
├── templates/
│
├── static/
│
├── utils/
│
├── migrations/
│
├── uploads/
│
├── alembic/
│
├── tests/
│
├── main.py
│
└── requirements.txt
```

---

# 🗄 Database

Main Tables

* users
* user_profiles
* communication_sessions
* interview_sessions
* grammar_sessions
* vocabulary_words
* vocabulary_progress
* public_speaking_sessions
* daily_challenges
* daily_challenge_submissions
* user_progress
* badges
* user_badges

---

# 🤖 AI Features

* Communication Evaluation
* Grammar Analysis
* Vocabulary Suggestions
* HR Interview Practice
* Technical Interview Practice
* Public Speaking Guidance
* Personalized Learning Recommendations
* Daily Challenges
* AI Feedback Generation

---

# 📊 Learning Analytics

The application tracks:

* Daily Practice
* Weekly Improvement
* Overall Progress
* Weak Areas
* Strong Areas
* Learning Streak
* Skill Growth

---

# 🔐 Authentication

* JWT Authentication
* Password Hashing
* Protected Routes
* Role-based Access (Future)

---

# 🚀 Future Enhancements

* Voice-based Interview Practice
* Speech-to-Text Analysis
* AI Pronunciation Coach
* Resume Review
* Cover Letter Generator
* AI Career Roadmap Generator
* Gamification
* Achievement Badges
* Leaderboards
* Multi-language Support
* Admin Dashboard

---

# 🧪 Installation

```bash
git clone https://github.com/yourusername/AI-SoftSkills-Coach.git

cd AI-SoftSkills-Coach
```

Create a virtual environment

```bash
python -m venv venv
```

Activate the environment

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure environment variables

```env
DATABASE_URL=mysql+pymysql://username:password@localhost/softskills_ai

SECRET_KEY=your_secret_key

AI_API_KEY=your_api_key
```

Run database migrations

```bash
alembic upgrade head
```

Start the server

```bash
uvicorn app.main:app --reload
```

---

# 📌 API Endpoints

## Authentication

* POST /register
* POST /login

## Communication

* POST /communication/practice
* GET /communication/history

## Interview

* POST /interview/start
* POST /interview/submit

## Grammar

* POST /grammar/check

## Vocabulary

* GET /vocabulary/daily

## Dashboard

* GET /dashboard

## Progress

* GET /progress

---

# 🎯 Learning Goals

This project demonstrates:

* REST API Development
* FastAPI
* SQLAlchemy ORM
* Alembic Migrations
* Authentication
* Prompt Engineering
* AI Integration
* Database Design
* Backend Architecture
* Clean Code Principles
* MVC Architecture
* Production-Level Project Structure

---

# 📸 Screenshots

> Screenshots and demo GIFs will be added as the project progresses.

---

# 🤝 Contributing

Contributions are welcome!

If you have suggestions or improvements, feel free to fork the repository and create a pull request.

---

# 📄 License

This project is licensed under the MIT License.

---

# ⭐ Support

If you found this project helpful, consider giving it a ⭐ on GitHub.

It motivates me to keep improving the project and adding new AI-powered learning features.
