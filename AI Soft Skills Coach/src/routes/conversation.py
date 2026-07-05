from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Generator, List


from src.db.db_config import Sessionlocal
from src.schemas.conversation import ConversationCreateResponse, ConversationItem, ConversationDetailResponse
from src.services.conversation_service import ConversationService
from src.services.dashboard_service import DashboardService

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

# Dependency to yield database sessions
async def get_db() -> Generator[AsyncSession, None, None]:
    async with Sessionlocal() as session:
        yield session

@router.post("/conversation", response_model=ConversationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated"
        )
    
    conv_service = ConversationService(db)
    new_conv = await conv_service.create_new_conversation(user.id)
    return {"conversation_id": new_conv.id}

@router.get("/conversation/{conversation_id}", response_model=None)
async def get_conversation_page_or_data(
    conversation_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "current_user", None)
    
    # Check if this is an API call requesting JSON
    is_json_request = "application/json" in request.headers.get("accept", "")
    
    if not user:
        if is_json_request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not authenticated"
            )
        return RedirectResponse(url="/login", status_code=303)
        
    conv_service = ConversationService(db)
    try:
        conversation_data = await conv_service.get_conversation(conversation_id, user.id)
    except HTTPException as exc:
        if is_json_request:
            raise exc
        raise exc

    if is_json_request:
        return conversation_data
        
    dashboard_service = DashboardService(db)
    dashboard_context = await dashboard_service.build_context(user, conversation_id)
    dashboard_context["request"] = request
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/chat.html",
        context=dashboard_context
    )

@router.get("/conversations", response_model=List[ConversationItem])
async def get_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated"
        )
    
    conv_service = ConversationService(db)
    conversations = await conv_service.get_user_conversations(user.id)
    return conversations

@router.post("/conversation/{conversation_id}/complete")
async def complete_conversation_session(
    conversation_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated"
        )
        
    conv_service = ConversationService(db)
    conv = await conv_service.conversation_repo.get_by_id(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    if conv.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Access denied to this conversation"
        )
        
    if conv.status != "completed":
        conv.status = "completed"
        conv.end_time = datetime.now()
        if conv.start_time:
            delta = conv.end_time - conv.start_time
            conv.duration_seconds = max(60, int(delta.total_seconds()))
        else:
            conv.duration_seconds = 120 # Default 2 minutes
        await db.commit()
        
    # Get latest analysis for this conversation
    from src.models.analysis import Analysis
    from src.models.message import Message
    
    analysis_result = await db.execute(
        select(Analysis).where(Analysis.conversation_id == conversation_id)
    )
    analysis = analysis_result.scalars().first()
    
    # Count messages
    msg_result = await db.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    )
    total_messages = msg_result.scalar() or 0
    
    # Get the homework assignment based on weak areas
    weak_topic = "Grammar & Vocab practice"
    if analysis and analysis.improvements:
        weak_topic = [i.strip() for i in analysis.improvements.split(",")][0]
        
    homework = f"Write down 5 sentences using proper '{weak_topic}' to summarize what you discussed today."
    
    return {
        "success": True,
        "report": {
            "topic": conv.topic,
            "duration_minutes": round((conv.duration_seconds or 120) / 60, 1),
            "total_messages": total_messages,
            "overall_score": int(analysis.overall_score) if analysis else 75,
            "metrics": {
                "grammar": int(analysis.grammar_score) if analysis else 70,
                "vocabulary": int(analysis.vocabulary_score) if analysis else 65,
                "fluency": int(analysis.fluency_score) if analysis else 68,
                "confidence": int(analysis.confidence_score) if analysis else 75,
                "pronunciation": int(analysis.pronunciation_score) if analysis else 72,
            },
            "mistakes": [s.strip() for s in analysis.improvements.split(",")] if analysis and analysis.improvements else ["Wrong Tense usage", "Missing prepositions"],
            "homework": homework
        }
    }
