from bson import ObjectId
from typing import List, Optional, Dict
from datetime import datetime, timezone

import mongoengine as me
from fastapi import HTTPException

from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, BulkChatMessageCreate
from app.services.client.client import ClientService
from app.services.client.client_channel import ClientChannelService
from app.models.mongodb.chat_message import ChatMessage, Attachment, SenderType
from app.models.mongodb.chat_session import ChatSession


def get_id_filter(message_id: str) -> Dict:

    if ObjectId.is_valid(message_id):
        return {"id": message_id}
    else:
        return {"external_id": message_id}


class ChatMessageService:
    @staticmethod
    def create_chat_message(message_data: ChatMessageCreate) -> ChatMessageResponse:
        from app.services.events.event_publisher import EventPublisher
        from app.models.mongodb.events.event_types import EventType
        from app.models.mongodb.channel_request_log import EntityType


        client = ClientService.get_client(message_data.client_id)
        client_channel = ClientChannelService.get_channel_by_type(
            client_id=message_data.client_id, channel_type=message_data.client_channel_type
        )
        try:
            session = ChatSession.objects.get(session_id=message_data.session_id)
        except me.DoesNotExist:
            session = ChatSession(session_id=message_data.session_id, client=client, client_channel=client_channel)
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
            external_id=message_data.external_id,
            config=message_data.config if isinstance(message_data.config, dict) else message_data.config.model_dump(),
        )
        chat_message.save()

        response = ChatMessageResponse.from_chat_message(chat_message)
        EventPublisher.publish(
            event_type=EventType.CHAT_MESSAGE_CREATED,
            entity_type=EntityType.CHAT_MESSAGE,
            entity_id=str(chat_message.id),
            parent_id=message_data.session_id,
            data=response,
        )

        return response

    @staticmethod
    def list_messages(
        id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        last_n: Optional[int] = None,
        sender_type: Optional[SenderType] = None,
        exclude_id: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ChatMessageResponse]:
        query = {}
        if id:
            query.update(get_id_filter(id))
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
        if start_date:
            query["created_at__gte"] = start_date
        if end_date:
            query["created_at__lte"] = end_date

        messages = ChatMessage.objects(**query).order_by("-created_at")
        if last_n:
            messages = messages[: last_n + 1]

        return [ChatMessageResponse.from_chat_message(msg) for msg in messages]

    @staticmethod
    def get_message(message_id: str) -> ChatMessage:
        try:
            chat_message = ChatMessage.objects.get(**get_id_filter(message_id))
            return chat_message
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Message not found")

    @staticmethod
    def update_chat_message(message_id: str, message_data: ChatMessageCreate) -> ChatMessageResponse:
        try:
            chat_message = ChatMessage.objects.get(**get_id_filter(message_id))
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
            client_id=bulk_message_data.client_id, channel_type=bulk_message_data.client_channel_type
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
