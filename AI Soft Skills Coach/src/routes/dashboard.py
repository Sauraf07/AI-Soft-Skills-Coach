from datetime import datetime
import os
from typing import Optional
from fastapi import APIRouter, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.db.db_config import Sessionlocal
from src.services.dashboard_service import DashboardService
from src.services.llm_service import LLMService
from src.services.tts_service import TTSService
from src.repository.conversation_repo import ConversationRepository
from src.repository.message_repo import MessageRepository
from src.repository.analysis_repo import AnalysisRepository
from src.repository.user_progress_repo import UserProgressRepository
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.analysis import Analysis

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

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

@router.post("/dashboard/message")
async def post_message(
    request: Request,
    message: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None)
):
    user = getattr(request.state, "current_user", None)
    if not user:
        return {"error": "Not authenticated"}, 401

    message_text = message
    audio_url = None
    
    if audio is not None and audio.filename:
        import uuid
        import os
        os.makedirs("src/static/audio/uploads", exist_ok=True)
        ext = os.path.splitext(audio.filename)[1] or ".webm"
        filename = f"user_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join("src/static/audio/uploads", filename)
        
        with open(filepath, "wb") as f:
            content = await audio.read()
            f.write(content)
            
        audio_url = f"/static/audio/uploads/{filename}"
        
        llm_service = LLMService()
        message_text = await llm_service.transcribe_audio(filepath)

    if not message_text or not message_text.strip():
        return {"error": "No message or audio content found."}, 400

    async with Sessionlocal() as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)
        analysis_repo = AnalysisRepository(session)
        progress_repo = UserProgressRepository(session)

        # Get or create active conversation
        conversation = await conv_repo.get_latest_by_user(user.id)
        if not conversation or conversation.status != "in_progress":
            conversation = Conversation(
                user_id=user.id,
                topic="New Conversation",
                start_time=datetime.now(),
                status="in_progress"
            )
            conversation = await conv_repo.create(conversation)

        # Rename conversation if it was named "New Conversation"
        if conversation.topic == "New Conversation":
            truncated_topic = (message_text[:30] + "...") if len(message_text) > 30 else message_text
            conversation.topic = truncated_topic
            await session.flush()

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            sender="user",
            message_text=message_text,
            message_type="audio" if audio_url else "text",
            audio_url=audio_url
        )
        await msg_repo.create(user_msg)

        # Fetch previous message history (ASC order — oldest first)
        db_messages = await msg_repo.get_by_conversation_id(conversation.id)
        # Exclude the last message (the one we just saved) from history
        history = []
        for m in db_messages[:-1]:
            history.append({"role": m.sender, "text": m.message_text})

        # Get response from LLM Coach
        llm_service = LLMService()
        coach_data = await llm_service.get_coach_response(message_text, history)
        ai_reply = coach_data.get("response", "")

        # Save AI response
        ai_msg = Message(
            conversation_id=conversation.id,
            sender="ai",
            message_text=ai_reply,
            message_type="text"
        )
        await msg_repo.create(ai_msg)

        # Synthesize AI response to speech
        tts_url = await TTSService.synthesize(ai_reply)

        # Save / Update Analysis
        scores = coach_data.get("scores", {})
        analysis = await analysis_repo.get_latest_by_conversation_id(conversation.id)
        
        feedback_text = coach_data.get("feedback", "")
        strengths_str = ", ".join(coach_data.get("strengths", []))
        improvements_str = ", ".join(coach_data.get("improvements", []))

        if not analysis:
            analysis = Analysis(
                conversation_id=conversation.id,
                grammar_score=scores.get("grammar", 80),
                vocabulary_score=scores.get("vocabulary", 80),
                confidence_score=scores.get("confidence", 80),
                fluency_score=scores.get("fluency", 80),
                pronunciation_score=scores.get("pronunciation", 80),
                overall_score=scores.get("overall", 80),
                feedback=feedback_text,
                strengths=strengths_str,
                improvements=improvements_str
            )
            await analysis_repo.create(analysis)
        else:
            analysis.grammar_score = scores.get("grammar", 80)
            analysis.vocabulary_score = scores.get("vocabulary", 80)
            analysis.confidence_score = scores.get("confidence", 80)
            analysis.fluency_score = scores.get("fluency", 80)
            analysis.pronunciation_score = scores.get("pronunciation", 80)
            analysis.overall_score = scores.get("overall", 80)
            analysis.feedback = feedback_text
            analysis.strengths = strengths_str
            analysis.improvements = improvements_str
            await session.flush()

        # Update UserProgress
        progress = await progress_repo.ensure_default_for_user(user.id)
        
        # Calculate stats across all user conversations
        all_convs = await conv_repo.get_recent_by_user(user.id, limit=100)
        total_convs = len(all_convs)
        
        total_score = 0.0
        scored_count = 0
        for c in all_convs:
            c_analysis = await analysis_repo.get_latest_by_conversation_id(c.id)
            if c_analysis and c_analysis.overall_score is not None:
                total_score += float(c_analysis.overall_score)
                scored_count += 1
                
        avg_score = (total_score / scored_count) if scored_count > 0 else float(scores.get("overall", 80))
        
        progress.total_conversations = total_convs
        progress.average_score = avg_score
        progress.total_minutes += 2
        progress.last_conversation_at = datetime.now()
        progress.current_streak = max(1, progress.current_streak)
        
        if progress.current_streak > progress.longest_streak:
            progress.longest_streak = progress.current_streak
            
        await session.commit()

        return {
            "success": True,
            "user_message": {
                "text": message_text,
                "time": user_msg.created_at.strftime("%I:%M %p") if isinstance(user_msg.created_at, datetime) else datetime.now().strftime("%I:%M %p"),
                "audio_url": audio_url
            },
            "ai_message": {
                "text": ai_reply,
                "time": datetime.now().strftime("%I:%M %p"),
                "audio_url": tts_url
            },
            "scores": {
                "overall": round(avg_score, 1),
                "grammar": scores.get("grammar", 80),
                "vocabulary": scores.get("vocabulary", 80),
                "fluency": scores.get("fluency", 80),
                "confidence": scores.get("confidence", 80),
                "pronunciation": scores.get("pronunciation", 80)
            },
            "grammar_suggestions": coach_data.get("grammar_suggestions", []),
            "feedback": feedback_text,
            "strengths": coach_data.get("strengths", []),
            "improvements": coach_data.get("improvements", [])
        }

@router.post("/dashboard/new-conversation")
async def start_new_conversation(request: Request):
    user = getattr(request.state, "current_user", None)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    async with Sessionlocal() as session:
        conv_repo = ConversationRepository(session)
        latest = await conv_repo.get_latest_by_user(user.id)
        if latest and latest.status == "in_progress":
            latest.status = "completed"
            latest.end_time = datetime.now()
            await session.commit()
            
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/dashboard/settings")
async def get_settings(request: Request):
    user = getattr(request.state, "current_user", None)
    if not user:
        return {"success": False, "error": "Not authenticated"}
    return {
        "success": True,
        "native_language": user.native_language,
        "groq_api_key": os.getenv("GROQ_API_KEY", "")
    }


@router.post("/dashboard/settings")
async def save_settings(
    request: Request,
    native_language: str = Form(...),
    groq_api_key: Optional[str] = Form(None)
):
    user = getattr(request.state, "current_user", None)
    if not user:
        return {"success": False, "error": "Not authenticated"}
        
    async with Sessionlocal() as session:
        from src.models.user import User
        db_user = await session.get(User, user.id)
        if db_user:
            db_user.native_language = native_language
            await session.commit()
            
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key.strip()
        # Also save to .env so it persists across server restarts
        try:
            env_path = ".env"
            content = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    content = f.readlines()
            
            groq_written = False
            for idx, line in enumerate(content):
                if line.startswith("GROQ_API_KEY="):
                    content[idx] = f"GROQ_API_KEY={groq_api_key.strip()}\n"
                    groq_written = True
                    break
            if not groq_written:
                content.append(f"\nGROQ_API_KEY={groq_api_key.strip()}\n")
            
            with open(env_path, "w") as f:
                f.writelines(content)
        except Exception as e:
            print("Failed to save Groq Key to .env file:", e)
        
    return {"success": True}
