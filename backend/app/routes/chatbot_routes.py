"""
Chatbot Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.models.database import get_db
from app.services.chatbot_service import ChatbotService
from app.utils.security import verify_token

router = APIRouter()
security = HTTPBearer()

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    entities: List[Dict[str, Any]]
    conversation_id: str
    chart_data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Get current user ID from token"""
    try:
        payload = verify_token(credentials.credentials)
        return int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    chat_message: ChatMessage,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Chat with the financial assistant bot"""
    chatbot_service = ChatbotService(db, user_id)
    
    try:
        response = await chatbot_service.process_message(
            message=chat_message.message,
            conversation_id=chat_message.conversation_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/conversations")
async def get_conversations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's chat conversation history"""
    chatbot_service = ChatbotService(db, user_id)
    
    conversations = await chatbot_service.get_conversation_history()
    
    return {"conversations": conversations}

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    chatbot_service = ChatbotService(db, user_id)
    
    success = await chatbot_service.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {"message": "Conversation deleted successfully"}

@router.get("/suggestions")
async def get_chat_suggestions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get personalized chat suggestions based on user's financial data"""
    chatbot_service = ChatbotService(db, user_id)
    
    suggestions = await chatbot_service.get_personalized_suggestions()
    
    return {"suggestions": suggestions}

@router.post("/feedback")
async def submit_chat_feedback(
    feedback_data: Dict[str, Any],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Submit feedback on chatbot responses"""
    chatbot_service = ChatbotService(db, user_id)
    
    await chatbot_service.record_feedback(feedback_data)
    
    return {"message": "Feedback recorded successfully"}