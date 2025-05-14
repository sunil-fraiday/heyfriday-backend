from fastapi import HTTPException, Depends, APIRouter, Query
from typing import Optional, Annotated

from app.schemas.chat_session_thread import ThreadResponse, ThreadListResponse
from app.api.v1.deps import verify_api_key
from app.services.chat.thread_manager import ThreadManager
from app.models.mongodb.chat_session import ChatSession

router = APIRouter(prefix="", tags=["Chat Session Threads"])


@router.post("/sessions/{session_id}/threads", response_model=ThreadResponse)
async def create_session_thread(
    session_id: str,
    inactivity_minutes: Annotated[Optional[int], Query(description="Override default inactivity minutes")] = None,
    api_key: str = Depends(verify_api_key),
):
    """Manually create a new thread for a session"""
    try:
        # Check if threading is enabled for this client
        threading_enabled, client_inactivity_minutes = ThreadManager.is_threading_enabled_for_session(session_id)
        if not threading_enabled:
            raise HTTPException(
                status_code=400,
                detail="Threading is not enabled for this client. Configure thread_config in the client settings.",
            )

        # Force creation of new thread
        thread = ThreadManager.create_new_thread(session_id)

        return ThreadResponse(
            thread_id=thread.thread_id,
            thread_session_id=thread.thread_session_id,
            parent_session_id=thread.parent_session_id,
            chat_session_id=str(thread.chat_session.id),
            active=thread.active,
            last_activity=thread.last_activity,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating thread: {str(e)}")


@router.get("/sessions/{session_id}/threads", response_model=ThreadListResponse)
async def list_session_threads(
    session_id: str,
    include_inactive: Annotated[bool, Query(description="Include inactive threads in the results")] = True,
    api_key: str = Depends(verify_api_key),
):
    """List all threads for a session"""
    try:
        # Check if threading is enabled for this client
        threading_enabled, _ = ThreadManager.is_threading_enabled_for_session(session_id)
        if not threading_enabled:
            raise HTTPException(
                status_code=400,
                detail="Threading is not enabled for this client. Configure thread_config in the client settings.",
            )

        parent_id, _ = ThreadManager.parse_session_id(session_id)

        threads = ThreadManager.list_threads(parent_id, include_inactive)
        thread_list = []

        for thread in threads:
            thread_list.append(
                ThreadResponse(
                    thread_id=thread.thread_id,
                    thread_session_id=thread.thread_session_id,
                    parent_session_id=thread.parent_session_id,
                    chat_session_id=str(thread.chat_session.id),
                    active=thread.active,
                    last_activity=thread.last_activity,
                )
            )

        return ThreadListResponse(threads=thread_list, total=len(thread_list))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing threads: {str(e)}")


@router.get("/sessions/{session_id}/active_thread", response_model=ThreadResponse)
async def get_active_thread(
    session_id: str,
    inactivity_minutes: Annotated[Optional[int], Query(description="Override default inactivity minutes")] = None,
    api_key: str = Depends(verify_api_key),
):
    """Get the active thread for a session, creating a new one if needed"""
    try:
        # Check if threading is enabled for this client
        threading_enabled, client_inactivity_minutes = ThreadManager.is_threading_enabled_for_session(session_id)
        if not threading_enabled:
            raise HTTPException(
                status_code=400,
                detail="Threading is not enabled for this client. Configure thread_config in the client settings.",
            )

        # Use provided hours or client default
        minutes_to_use = inactivity_minutes if inactivity_minutes is not None else client_inactivity_minutes

        parent_id, _ = ThreadManager.parse_session_id(session_id)

        # Check for the latest thread
        latest_thread = ThreadManager.get_latest_thread(parent_id)

        # If no thread or thread is inactive, create new one
        if not latest_thread or not latest_thread.is_active(minutes_to_use):
            thread = ThreadManager.create_new_thread(parent_id)
        else:
            thread = latest_thread
            thread.update_activity()

        return ThreadResponse(
            thread_id=thread.thread_id,
            thread_session_id=thread.thread_session_id,
            parent_session_id=thread.parent_session_id,
            chat_session_id=str(thread.chat_session.id),
            active=thread.active,
            last_activity=thread.last_activity,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active thread: {str(e)}")


@router.post("/sessions/{session_id}/resolve_thread")
async def resolve_thread_for_message(
    session_id: str,
    inactivity_minutes: Annotated[Optional[int], Query(description="Override default inactivity minutes")] = None,
    force_new: Annotated[bool, Query(description="Force creation of a new thread even if current is active")] = False,
    api_key: str = Depends(verify_api_key),
):
    """
    Resolve the appropriate session thread to use for a message.

    If threading is enabled for the client, this will return the appropriate thread session.
    If threading is disabled, it will return the original session.
    """
    try:
        # Get the active thread's session for this message or the original session if threading disabled
        threading_enabled, client_inactivity_minutes = ThreadManager.is_threading_enabled_for_session(session_id)
        if not threading_enabled:
            raise HTTPException(
                status_code=400,
                detail="Threading is not enabled for this client. Configure thread_config in the client settings.",
            )
        chat_session = ThreadManager.get_or_create_active_thread(
            session_id=session_id, force_new=force_new, inactivity_minutes=inactivity_minutes
        )

        # Always return a consistent response structure whether threading is used or not
        return {"session_id": chat_session.session_id, "mongodb_id": str(chat_session.id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving thread: {str(e)}")
