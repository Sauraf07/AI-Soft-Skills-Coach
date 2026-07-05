from datetime import datetime
from pydantic import BaseModel
from typing import List

class ConversationCreateResponse(BaseModel):
    conversation_id: int

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    topic: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationItem(BaseModel):
    id: int
    topic: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    sender: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]
