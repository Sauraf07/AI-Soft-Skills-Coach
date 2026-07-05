from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, desc, func
from src.repository.analysis_repo import AnalysisRepository
from src.repository.conversation_repo import ConversationRepository
from src.repository.message_repo import MessageRepository
from src.repository.user_progress_repo import UserProgressRepository
from src.utils.session import build_profile

DEFAULT_CHAT_MESSAGES = [
    {
        "role": "assistant",
        "author": "AI Coach",
        "avatar": "bi-robot",
        "time": "Now",
        "text": "Hello! 👋 I'm your AI soft skills coach. Let's start practicing your communication skills today!",
        "audio": "",
        "status": "",
    }
]

DEFAULT_PROGRESS = {
    "overall": 0,
    "metrics": [
        {"label": "Fluency", "score": 0, "tone": "primary", "icon": "bi-stars"},
        {"label": "Grammar", "score": 0, "tone": "success", "icon": "bi-book"},
        {"label": "Vocabulary", "score": 0, "tone": "warning", "icon": "bi-chat-square-text"},
        {"label": "Pronunciation", "score": 0, "tone": "info", "icon": "bi-mic"},
        {"label": "Confidence", "score": 0, "tone": "accent", "icon": "bi-emoji-smile"},
    ],
}

DEFAULT_RECENT_CONVERSATIONS = []

DEFAULT_QUICK_PROMPTS = [
    "Tell me about a time you solved a difficult problem",
    "Describe your career goals for the next five years",
    "Let's practice a mock job interview",
]


class DashboardService:
    def __init__(self, session):
        self.session = session
        self.progress_repo = UserProgressRepository(session)
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.analysis_repo = AnalysisRepository(session)

    async def build_context(self, user, conversation_id: Optional[int] = None):
        if not user:
            return {
                "profile": {"name": "Guest", "level": "Beginner", "initials": "G"},
                "progress": DEFAULT_PROGRESS,
                "recent_conversations": DEFAULT_RECENT_CONVERSATIONS,
                "quick_prompts": DEFAULT_QUICK_PROMPTS,
                "chat_messages": DEFAULT_CHAT_MESSAGES,
                "analysis": None,
                "daily_goal": None,
                "vocab": None,
                "weak_areas": [],
                "recommendation": None,
                "badges": []
            }

        from src.models.learning_goal import LearningGoal
        from src.models.vocabulary_word import VocabularyWord
        from src.models.achievement import Achievement
        from src.models.analysis import Analysis
        from src.models.conversation import Conversation
        from src.models.message import Message

        # 1. Fetch Daily Goal Progress
        today_date = date.today()
        goal_result = await self.session.execute(
            select(LearningGoal)
            .where(LearningGoal.user_id == user.id, LearningGoal.status == "active")
        )
        active_goal = goal_result.scalars().first()
        if not active_goal:
            active_goal = LearningGoal(
                user_id=user.id,
                title="Practice Speaking",
                description="Speak for 10 minutes",
                target_score=10,
                start_date=today_date,
                status="active"
            )
            self.session.add(active_goal)
            await self.session.commit()

        # Sum speaking time today
        convs_today_result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id, Conversation.created_at >= datetime.combine(today_date, datetime.min.time()))
        )
        convs_today = convs_today_result.scalars().all()
        total_seconds_today = sum(c.duration_seconds or 0 for c in convs_today)
        
        if total_seconds_today == 0:
            msg_count_result = await self.session.execute(
                select(func.count(Message.id))
                .join(Conversation)
                .where(Conversation.user_id == user.id, Message.sender == "user", Message.created_at >= datetime.combine(today_date, datetime.min.time()))
            )
            user_msg_count = msg_count_result.scalar() or 0
            minutes_today = round(min(10.0, float(user_msg_count)), 1)
        else:
            minutes_today = round(total_seconds_today / 60, 1)

        goal_target = active_goal.target_score or 10
        goal_percent = min(100, int((minutes_today / goal_target) * 100))
        goal_completed = minutes_today >= goal_target

        daily_goal_widget = {
            "title": active_goal.title,
            "target": goal_target,
            "current": minutes_today,
            "percent": goal_percent,
            "completed": goal_completed,
            "status_text": f"{minutes_today} / {goal_target} minutes spoken today"
        }

        # 2. Vocabulary Card
        vocab_result = await self.session.execute(
            select(VocabularyWord)
            .where(VocabularyWord.user_id == user.id)
            .order_by(desc(VocabularyWord.created_at))
        )
        latest_vocab = vocab_result.scalars().first()
        if not latest_vocab:
            latest_vocab = VocabularyWord(
                user_id=user.id,
                word="Enthusiastic",
                meaning="Very excited and interested.",
                example="I am enthusiastic about learning Python."
            )
            self.session.add(latest_vocab)
            await self.session.commit()

        vocab_widget = {
            "word": latest_vocab.word,
            "meaning": latest_vocab.meaning,
            "example": latest_vocab.example
        }

        # 3. Weak Areas & Recommendations
        analyses_result = await self.session.execute(
            select(Analysis)
            .join(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(desc(Analysis.id))
            .limit(3)
        )
        recent_analyses = analyses_result.scalars().all()
        
        weak_areas = []
        for anal in recent_analyses:
            if anal.improvements:
                improvements_list = [imp.strip() for imp in anal.improvements.split(",")]
                for imp in improvements_list:
                    if imp and imp not in weak_areas:
                        weak_areas.append(imp)
        
        if not weak_areas:
            weak_areas = ["Past Tense", "Indefinite Articles", "Vocabulary Range"]
            
        first_weak = weak_areas[0]
        rec_practice = {
            "topic": f"{first_weak} Practice",
            "duration": "8 Minutes"
        }

        # 4. Achievements
        total_conv_result = await self.session.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user.id)
        )
        total_convs = total_conv_result.scalar() or 0

        ach_result = await self.session.execute(
            select(Achievement)
            .where(Achievement.user_id == user.id)
        )
        earned_ach_titles = [ach.title for ach in ach_result.scalars().all()]

        available_badges = [
            {"title": "First Talk", "description": "Start 1 conversation", "icon": "🏅", "req_conv": 1},
            {"title": "Speech Explorer", "description": "Start 5 conversations", "icon": "🚀", "req_conv": 5},
            {"title": "Communication Master", "description": "Start 10 conversations", "icon": "🏆", "req_conv": 10}
        ]

        badges_widget = []
        for badge in available_badges:
            is_earned = badge["title"] in earned_ach_titles
            if not is_earned and total_convs >= badge["req_conv"]:
                new_ach = Achievement(
                    user_id=user.id,
                    title=badge["title"],
                    description=badge["description"],
                    icon=badge["icon"]
                )
                self.session.add(new_ach)
                await self.session.commit()
                is_earned = True
            
            badges_widget.append({
                "title": badge["title"],
                "description": badge["description"],
                "icon": badge["icon"],
                "earned": is_earned
            })

        # 5. Average Scores query (Phase 4)
        avg_scores_result = await self.session.execute(
            select(
                func.avg(Analysis.grammar_score),
                func.avg(Analysis.vocabulary_score),
                func.avg(Analysis.confidence_score),
                func.avg(Analysis.fluency_score),
                func.avg(Analysis.pronunciation_score),
                func.avg(Analysis.overall_score)
            )
            .join(Conversation)
            .where(Conversation.user_id == user.id)
        )
        avg_row = avg_scores_result.first()
        
        averages = {
            "grammar": round(float(avg_row[0]), 0) if avg_row and avg_row[0] is not None else None,
            "vocabulary": round(float(avg_row[1]), 0) if avg_row and avg_row[1] is not None else None,
            "confidence": round(float(avg_row[2]), 0) if avg_row and avg_row[2] is not None else None,
            "fluency": round(float(avg_row[3]), 0) if avg_row and avg_row[3] is not None else None,
            "pronunciation": round(float(avg_row[4]), 0) if avg_row and avg_row[4] is not None else None,
            "overall": round(float(avg_row[5]), 0) if avg_row and avg_row[5] is not None else None,
        }

        # 6. Fetch basic widgets
        progress = await self.progress_repo.ensure_default_for_user(user.id)
        recent_conversations = await self.conversation_repo.get_recent_by_user(
            user.id, limit=3
        )
        
        if conversation_id is not None:
            active_conversation = await self.conversation_repo.get_by_id(conversation_id)
            if active_conversation and active_conversation.user_id != user.id:
                active_conversation = None
        else:
            active_conversation = await self.conversation_repo.get_latest_by_user(user.id)

        if active_conversation is not None:
            latest_messages = await self.message_repo.get_by_conversation_id(
                active_conversation.id
            )
            latest_analysis = await self.analysis_repo.get_latest_by_conversation_id(
                active_conversation.id
            )
        else:
            latest_messages = []
            latest_analysis = None

        profile = build_profile(user, progress)
        progress_widget = self._build_progress_widget(progress, averages)
        recent_widget = self._build_recent_conversations(recent_conversations)
        chat_widget = (
            self._build_chat_messages(latest_messages) or DEFAULT_CHAT_MESSAGES
        )

        analysis_data = None
        if latest_analysis is not None:
            analysis_data = {
                "feedback": latest_analysis.feedback or "",
                "strengths": [s.strip() for s in latest_analysis.strengths.split(",")] if latest_analysis.strengths else [],
                "improvements": [i.strip() for i in latest_analysis.improvements.split(",")] if latest_analysis.improvements else []
            }

        return {
            "profile": profile,
            "progress": progress_widget,
            "recent_conversations": recent_widget or DEFAULT_RECENT_CONVERSATIONS,
            "quick_prompts": DEFAULT_QUICK_PROMPTS,
            "chat_messages": chat_widget,
            "analysis": analysis_data,
            "daily_goal": daily_goal_widget,
            "vocab": vocab_widget,
            "weak_areas": weak_areas,
            "recommendation": rec_practice,
            "badges": badges_widget
        }

    def _build_progress_widget(self, progress, averages):
        overall = averages["overall"] if averages["overall"] is not None else (
            float(progress.average_score) if progress.average_score is not None else 0.0
        )

        metrics = [
            {
                "label": "Fluency",
                "score": int(averages["fluency"]) if averages["fluency"] is not None else 70,
                "tone": "primary",
                "icon": "bi-stars",
            },
            {
                "label": "Grammar",
                "score": int(averages["grammar"]) if averages["grammar"] is not None else 65,
                "tone": "success",
                "icon": "bi-book",
            },
            {
                "label": "Vocabulary",
                "score": int(averages["vocabulary"]) if averages["vocabulary"] is not None else 60,
                "tone": "warning",
                "icon": "bi-chat-square-text",
            },
            {
                "label": "Pronunciation",
                "score": int(averages["pronunciation"]) if averages["pronunciation"] is not None else 55,
                "tone": "info",
                "icon": "bi-mic",
            },
            {
                "label": "Confidence",
                "score": int(averages["confidence"]) if averages["confidence"] is not None else 75,
                "tone": "accent",
                "icon": "bi-emoji-smile",
            },
        ]
        return {"overall": round(overall, 1), "metrics": metrics}

    def _build_recent_conversations(self, conversations):
        result = []
        tones = ["violet", "green", "orange"]

        for index, conversation in enumerate(conversations):
            result.append(
                {
                    "title": conversation.topic,
                    "time": self._format_time(conversation.created_at),
                    "icon": "bi-chat-dots",
                    "tone": tones[index % len(tones)],
                }
            )

        return result

    def _build_chat_messages(self, messages):
        result = []
        for message in messages:
            result.append(
                {
                    "role": "user" if message.sender == "user" else "assistant",
                    "author": "You" if message.sender == "user" else "AI Coach",
                    "avatar": (
                        "bi-person-circle" if message.sender == "user" else "bi-robot"
                    ),
                    "time": self._format_time(message.created_at),
                    "text": message.message_text,
                    "audio": "00:05",
                    "status": "read" if message.sender == "user" else "",
                }
            )

        return result

    @staticmethod
    def _score(value):
        return round(float(value), 2) if value is not None else 0.0

    @staticmethod
    def _format_time(value):
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%I:%M %p")
        return str(value)
