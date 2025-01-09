from fastapi import APIRouter, Query
from typing import List, Optional

from app.services.chat.message import ChatMessageService
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, BulkChatMessageCreate
from app.tasks.chat import trigger_chat_workflow, trigger_suggestion_workflow

router = APIRouter(prefix="/messages", tags=["Chat Messages"])


@router.post("", response_model=ChatMessageResponse)
async def create_message(message_data: ChatMessageCreate):
    print("Received message data:", message_data.model_dump_json())
    chat_message = ChatMessageService.create_chat_message(message_data)

    ai_enabled = chat_message.config.get("ai_enabled", True)
    suggestion_mode = chat_message.config.get("suggestion_mode", False)

    if ai_enabled and not suggestion_mode:
        trigger_chat_workflow(message_id=str(chat_message.id))
    elif not ai_enabled and suggestion_mode:
        trigger_suggestion_workflow(message_id=str(chat_message.id))

    return chat_message


@router.get("", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: Optional[str] = Query(None), user_id: Optional[str] = Query(None), last_n: Optional[int] = Query(None)
):
    return ChatMessageService.list_messages(session_id=session_id, user_id=user_id, last_n=last_n)


@router.put("/{message_id}", response_model=ChatMessageResponse)
async def update_message(message_id: str, message_data: ChatMessageCreate):
    return ChatMessageService.update_chat_message(message_id, message_data)


@router.post("/bulk", response_model=List[ChatMessageResponse])
async def create_bulk_messages(bulk_message_data: BulkChatMessageCreate):
    chat_message_bulk_create_response = ChatMessageService.create_bulk_chat_messages(bulk_message_data)
    latest_message = max(chat_message_bulk_create_response, key=lambda x: x.created_at)
    trigger_chat_workflow(message_id=str(latest_message.id))
    return chat_message_bulk_create_response
