from typing import List
from datetime import datetime
from datetime import timezone

import mongoengine as me
from fastapi import HTTPException, APIRouter

from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, AttachmentCreate
from app.models.mongodb.chat_message import ChatMessage, Attachment, MessageCategory
from app.models.mongodb.chat_session import ChatSession

router = APIRouter(prefix="/sessions", tags=["Chat Messages"])

# TODO: Refactor all API logic into services


@router.post("/{session_id}/messages", response_model=ChatMessageResponse)
async def create_chat_message(message_data: ChatMessageCreate):
    # Get or create chat session
    if message_data.session_id:
        try:
            session = ChatSession.objects.get(session_id=message_data.session_id)
        except me.DoesNotExist:
            session = ChatSession(session_id=message_data.session_id)
            session.save()
    else:
        session = ChatSession(session_id=message_data.session_id)
        session.save()

    attachments = []
    if message_data.attachments:
        for attach in message_data.attachments:
            attachments.append(Attachment(**attach.model_dump()))

    chat_message = ChatMessage(
        session=session,
        text=message_data.text,
        sender=message_data.sender,
        sender_name=message_data.sender_name,
        attachments=attachments,
        sql_data=message_data.sql_data,
        category=message_data.category.value,
    )
    chat_message.save()

    return ChatMessageResponse(
        id=str(chat_message.id),
        created_at=chat_message.created_at,
        updated_at=chat_message.updated_at,
        sender=chat_message.sender,
        sender_name=chat_message.sender_name,
        session_id=str(session.id),
        text=chat_message.text,
        attachments=[AttachmentCreate(**a) for a in chat_message.attachments] if chat_message.attachments else None,
        category=MessageCategory(chat_message.category),
        edit=chat_message.edit,
    )


@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(session_id: str):
    try:
        session = ChatSession.objects.get(session_id=session_id)
    except me.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = ChatMessage.objects(session=session).order_by("created_at")

    return [
        ChatMessageResponse(
            id=str(msg.id),
            created_at=msg.created_at,
            updated_at=msg.updated_at,
            sender=msg.sender,
            sender_name=msg.sender_name,
            session_id=str(session.id),
            text=msg.text,
            attachments=[AttachmentCreate(**a) for a in msg.attachments] if msg.attachments else None,
            category=MessageCategory(msg.category),
            edit=msg.edit,
        )
        for msg in messages
    ]


@router.put("/{session_id}/messages/{message_id}", response_model=ChatMessageResponse)
async def update_chat_message(message_id: str, message_data: ChatMessageCreate):
    try:
        chat_message = ChatMessage.objects.get(session_id=message_id)
    except me.DoesNotExist:
        raise HTTPException(status_code=404, detail="Message not found")

    # Update message fields
    chat_message.text = message_data.text
    chat_message.sender = message_data.sender
    chat_message.sender_name = message_data.sender_name
    chat_message.updated_at = datetime.now(timezone.utc)
    chat_message.edit = True

    # Update attachments if provided
    if message_data.attachments:
        attachments = []
        for attach in message_data.attachments:
            attachments.append(Attachment(**attach.dict()))
        chat_message.attachments = attachments

    # Update SQL data if provided
    if message_data.sql_data:
        chat_message.sql_data = message_data.sql_data

    chat_message.save()

    return ChatMessageResponse(
        id=str(chat_message.id),
        created_at=chat_message.created_at,
        updated_at=chat_message.updated_at,
        sender=chat_message.sender,
        sender_name=chat_message.sender_name,
        session_id=str(chat_message.session.id),
        text=chat_message.text,
        attachments=[AttachmentCreate(**a) for a in chat_message.attachments] if chat_message.attachments else None,
        category=MessageCategory(chat_message.category),
        edit=chat_message.edit,
    )
