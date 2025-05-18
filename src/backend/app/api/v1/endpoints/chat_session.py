import mongoengine as me
from fastapi import HTTPException, Depends, APIRouter, Query
from typing import Optional, Annotated
from datetime import datetime

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_message import ChatMessage
from app.schemas.chat_session import ChatSessionResponse, ChatSessionListResponse
from app.api.v1.deps import verify_api_key
from app.utils.logger import get_logger

router = APIRouter(prefix="", tags=["Chat Sessions"])
logger = get_logger(__name__)


@router.post("/sessions", response_model=dict)
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
            "active": session.active,
        }
    except me.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    client_id: Annotated[Optional[str], Query(description="Filter by client ID")] = None,
    client_channel: Annotated[Optional[str], Query(description="Filter by client channel")] = None,
    user_id: Annotated[Optional[str], Query(description="Filter by user ID (sender)")] = None,
    active: Annotated[Optional[bool], Query(description="Filter by active status")] = None,
    start_date: Annotated[Optional[datetime], Query(description="Filter sessions created after this date")] = None,
    end_date: Annotated[Optional[datetime], Query(description="Filter sessions created before this date")] = None,
    skip: Annotated[int, Query(description="Number of records to skip", ge=0)] = 0,
    limit: Annotated[int, Query(description="Maximum number of records to return", ge=1, le=100)] = 10,
    api_key: str = Depends(verify_api_key),
):
    """
    List chat sessions with optional filtering by client_id, client_channel, user_id, active status,
    and date range (start_date and end_date).
    """
    try:
        # Validate date range if both dates provided
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=400, detail="Invalid date range: end_date cannot be earlier than start_date"
            )

        query_filter = {}
        if client_id:
            query_filter["client"] = client_id
        if client_channel:
            query_filter["client_channel"] = client_channel
        if active is not None:
            query_filter["active"] = active

        # Add date range filters
        if start_date:
            query_filter["updated_at__gte"] = start_date
        if end_date:
            query_filter["updated_at__lte"] = end_date

        if user_id:
            unique_sessions = ChatMessage.objects.filter(sender=user_id).distinct("session")

            if unique_sessions:
                query_filter["id__in"] = [str(session.id) for session in unique_sessions]
            else:
                return ChatSessionListResponse(sessions=[], total=0)

        logger.info(f"Query filter: {query_filter}")
        # Get total count for pagination metadata
        total = ChatSession.objects.filter(**query_filter).count()

        # Query with pagination - order by updated_at descending (newest first)
        sessions = ChatSession.objects.filter(**query_filter).order_by("-updated_at").skip(skip).limit(limit).all()

        # Format the response
        session_list = []
        for session in sessions:
            session_list.append(
                ChatSessionResponse(
                    id=str(session.id),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    session_id=str(session.session_id),
                    active=session.active,
                    client=str(session.client.id) if session.client else None,
                    client_channel=str(session.client_channel.id) if session.client_channel else None,
                    participants=session.participants,
                )
            )

        return ChatSessionListResponse(sessions=session_list, total=total)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status codes and messages
        raise
    except Exception as e:
        # Catch all other exceptions and convert them to 500 errors
        raise HTTPException(status_code=500, detail=f"Error listing chat sessions: {str(e)}")
