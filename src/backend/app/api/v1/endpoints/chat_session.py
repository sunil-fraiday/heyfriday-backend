import mongoengine as me
from fastapi import HTTPException, Depends, APIRouter

from app.models.mongodb.chat_session import ChatSession

router = APIRouter(prefix="", tags=["Chat Sessions"])


@router.post("/sessions/", response_model=dict)
async def create_chat_session():
    session = ChatSession()
    session.save()
    return {"session_id": str(session.id)}


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    try:
        session = ChatSession.objects.get(id=session_id)
        return {
            "id": str(session.id),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "participants": session.participants,
            "active": session.active,
        }
    except me.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")
