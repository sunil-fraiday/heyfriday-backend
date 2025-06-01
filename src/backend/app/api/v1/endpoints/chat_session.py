import mongoengine as me
from fastapi import HTTPException, Depends, APIRouter, Query
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_message import ChatMessage
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_types import EventType
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
    session_id: Annotated[Optional[str], Query(description="Filter by session ID (supports partial matching)")] = None,
    active: Annotated[Optional[bool], Query(description="Filter by active status")] = None,
    handover: Annotated[
        Optional[bool], Query(description="Filter sessions that were handed over to human agents")
    ] = None,
    start_date: Annotated[Optional[datetime], Query(description="Filter sessions created after this date")] = None,
    end_date: Annotated[Optional[datetime], Query(description="Filter sessions created before this date")] = None,
    skip: Annotated[int, Query(description="Number of records to skip", ge=0)] = 0,
    limit: Annotated[int, Query(description="Maximum number of records to return", ge=1, le=100)] = 10,
    api_key: str = Depends(verify_api_key),
):
    """
    List chat sessions with optional filtering by client_id, client_channel, user_id, active status,
    human handover status, and date range (start_date and end_date).
    """
    try:
        # Validate date range if both dates provided
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status_code=400, detail="Invalid date range: end_date cannot be earlier than start_date"
            )

        # Build the aggregation pipeline
        pipeline = []
        match_stage = {}
        
        # Standard filters
        if client_id:
            match_stage["client"] = ObjectId(client_id)
        if client_channel:
            match_stage["client_channel"] = ObjectId(client_channel)
        if active is not None:
            match_stage["active"] = active
        if start_date:
            match_stage["updated_at"] = {"$gte": start_date}
        if end_date:
            if "updated_at" in match_stage:
                match_stage["updated_at"]["$lte"] = end_date
            else:
                match_stage["updated_at"] = {"$lte": end_date}
        
        # Session ID filtering with partial matching
        if session_id:
            # Apply regex matching directly to the session_id field
            # No need to convert since session_id is already a string
            match_stage["session_id"] = {"$regex": session_id, "$options": "i"}  # Case-insensitive partial matching
        
        # User ID filter requires a lookup to messages collection
        if user_id:
            # Get session IDs with messages from this user
            unique_sessions = ChatMessage.objects.filter(sender=user_id).distinct("session")
            if not unique_sessions:
                return ChatSessionListResponse(sessions=[], total=0)
            
            match_stage["_id"] = {"$in": [session.id for session in unique_sessions]}
        
        # Add the match stage if we have any filters
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        # Always add a lookup stage to get handover events for each session
        pipeline.extend([
            # Lookup handover events where session ID is the parent_id
            {"$lookup": {
                "from": "events",
                "let": {"session_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$and": [
                            {"$eq": ["$parent_id", "$$session_id"]},
                            {"$eq": ["$event_type", EventType.CHAT_WORKFLOW_HANDOVER.value]}
                        ]}
                    }}
                ],
                "as": "handover_events"
            }},
            
            # Add a field to indicate if there are handover events
            {"$addFields": {
                "has_handover": {"$cond": {
                    "if": {"$gt": [{"$size": "$handover_events"}, 0]},
                    "then": True,
                    "else": False
                }}
            }}
        ])
        
        # Only filter by handover status if the parameter is provided
        if handover is not None:
            pipeline.append({"$match": {"has_handover": handover}})
        
        # Base pipeline with all filters
        pipeline = pipeline

        # Create query pipeline with sorting and pagination
        query_pipeline = pipeline.copy()
        query_pipeline.extend([
            {"$sort": {"updated_at": -1}},  # Sort by updated_at descending
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        # Create count pipeline for total count
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        
        # Execute the aggregation pipeline
        logger.info(f"Aggregation pipeline: {query_pipeline}")
        session_cursor = ChatSession.objects.aggregate(query_pipeline)
        sessions = list(session_cursor)
        
        count_result = list(ChatSession.objects.aggregate(count_pipeline))
        total = count_result[0]["total"] if count_result else 0
        
        # Format the response
        session_list = []
        for session_doc in sessions:
            session_list.append(
                ChatSessionResponse(
                    id=str(session_doc["_id"]),
                    created_at=session_doc.get("created_at"),
                    updated_at=session_doc.get("updated_at"),
                    session_id=str(session_doc.get("session_id", "")),
                    active=session_doc.get("active", False),
                    client=str(session_doc["client"]) if "client" in session_doc and session_doc["client"] else None,
                    client_channel=str(session_doc["client_channel"]) if "client_channel" in session_doc and session_doc["client_channel"] else None,
                    participants=session_doc.get("participants", []),
                    handover=session_doc.get("has_handover", False)
                )
            )

        return ChatSessionListResponse(sessions=session_list, total=total)
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status codes and messages
        raise
    except Exception as e:
        # Catch all other exceptions and convert them to 500 errors
        raise HTTPException(status_code=500, detail=f"Error listing chat sessions: {str(e)}")
