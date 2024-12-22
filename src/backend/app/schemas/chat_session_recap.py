from pydantic import BaseModel
from datetime import datetime
from typing import List


class ParticipantInfo(BaseModel):
    name: str
    role: str
    contribution: str


class SentimentInfo(BaseModel):
    sentiment: str
    communication_notes: str


class AttachmentInfo(BaseModel):
    type: str
    description: str


class AgreementInfo(BaseModel):
    promise: str
    details: str


class RecapData(BaseModel):
    context_of_issue: str
    conversation_highlights: List[str]
    participants_and_roles: List[ParticipantInfo]
    client_sentiment_and_communication_notes: SentimentInfo
    unresolved_points: List[str]
    attachments_and_evidence: List[AttachmentInfo]
    important_agreements_or_promises: List[AgreementInfo]

    class Config:
        from_attributes = True


class ChatSessionRecapResponse(BaseModel):
    id: str
    session_id: str
    recap_data: RecapData
    created_at: datetime
    updated_at: datetime
