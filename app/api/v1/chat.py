from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import handle_chat
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    vector_store=Depends(get_vector_store),
):
    result = await handle_chat(
        session=session,
        vector_store=vector_store,
        user_id=current_user.id,
        message=request.message,
        conversation_history=[m.model_dump() for m in request.conversation_history],
    )
    return result
