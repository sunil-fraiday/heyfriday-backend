from typing import List, Optional
from datetime import datetime, timezone

import mongoengine as me
from fastapi import HTTPException

from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, BulkChatMessageCreate
from app.services.client.client import ClientService
from app.services.client.client_channel import ClientChannelService
from app.models.mongodb.chat_message import ChatMessage, Attachment, SenderType
from app.models.mongodb.chat_session import ChatSession


class ChatMessageService:
    @staticmethod
    def create_chat_message(message_data: ChatMessageCreate) -> ChatMessageResponse:
        try:
            session = ChatSession.objects.get(session_id=message_data.session_id)
        except me.DoesNotExist:
            session = ChatSession(session_id=message_data.session_id)
            session.save()

        attachments = (
            [Attachment(**attach.model_dump()) for attach in message_data.attachments]
            if message_data.attachments
            else []
        )

        # Create the chat message
        chat_message = ChatMessage(
            session=session,
            text=message_data.text,
            sender=message_data.sender,
            sender_name=message_data.sender_name,
            attachments=attachments,
            category=message_data.category.value,
        )
        chat_message.save()

        return ChatMessageResponse.from_chat_message(chat_message)

    @staticmethod
    def list_messages(
        id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        last_n: Optional[int] = None,
        sender_type: Optional[SenderType] = None,
        exclude_id: Optional[List[str]] = None,
    ) -> List[ChatMessageResponse]:
        query = {}
        if id:
            query["id"] = id
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id)
            except me.DoesNotExist as e:
                raise HTTPException(status_code=404, detail="Chat Session not found")
            query["session"] = chat_session.id
        if user_id:
            query["sender"] = user_id
        if sender_type:
            query["sender_type"] = sender_type.value
        if exclude_id:
            query["id__nin"] = exclude_id

        messages = ChatMessage.objects(**query).order_by("-created_at")
        if last_n:
            messages = messages[:last_n]

        return [ChatMessageResponse.from_chat_message(msg) for msg in messages]

    @staticmethod
    def get_message(message_id: str) -> ChatMessageResponse:
        try:
            chat_message = ChatMessage.objects.get(id=message_id)
            return ChatMessageResponse.from_chat_message(chat_message)
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Message not found")

    @staticmethod
    def update_chat_message(message_id: str, message_data: ChatMessageCreate) -> ChatMessageResponse:
        try:
            chat_message = ChatMessage.objects.get(id=message_id)
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Message not found")

        chat_message.text = message_data.text
        chat_message.sender = message_data.sender
        chat_message.sender_name = message_data.sender_name
        chat_message.updated_at = datetime.now(timezone.utc)
        chat_message.edit = True

        if message_data.attachments:
            chat_message.attachments = [Attachment(**attach.dict()) for attach in message_data.attachments]

        if message_data.sql_data:
            chat_message.sql_data = message_data.sql_data

        chat_message.save()

        return ChatMessageResponse.from_chat_message(chat_message)

    @staticmethod
    def create_bulk_chat_messages(bulk_message_data: BulkChatMessageCreate) -> List[ChatMessageResponse]:
        responses = []
        session = None
        client = ClientService.get_client(bulk_message_data.client_id)
        client_channel = ClientChannelService.get_channel_by_type(
            client_id=bulk_message_data.client_id, client_channel=bulk_message_data.client_channel_type
        )

        try:
            session = ChatSession.objects.get(
                session_id=bulk_message_data.session_id, client=client, client_channel=client_channel
            )
        except me.DoesNotExist:
            session = ChatSession(
                session_id=bulk_message_data.session_id,
                client=client,
                client_channel=client_channel,
            )
            session.save()

        for message_data in bulk_message_data.messages:
            attachments = (
                [Attachment(**attach.model_dump()) for attach in message_data.attachments]
                if message_data.attachments
                else []
            )

            chat_message = ChatMessage(
                session=session,
                text=message_data.text,
                sender=message_data.sender,
                sender_name=message_data.sender_name,
                attachments=attachments,
                category=message_data.category.value,
                created_at=message_data.created_at or datetime.now(timezone.utc),
            )
            chat_message.save()
            responses.append(chat_message)

        return [ChatMessageResponse.from_chat_message(msg) for msg in responses]
