import json
from typing import List, Dict, Optional
import traceback

from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from app.utils.logger import get_logger
from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_session_recap import ChatSessionRecap, ExecutionStatus
from app.schemas.chat import ChatMessageResponse

from .prompt import CHAT_RECAP_PROMPT_TEMPLATE, SYSTEM_PROMPT

logger = get_logger(__name__)


class ChatRecapService:
    def __init__(
        self,
        aws_runtime: str,
        region_name: str,
        access_key_id: str,
        secret_access_key: str,
        model_name: str,
    ):
        self.aws_runtime = aws_runtime
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.model_name = model_name

        self.model = ChatBedrock(
            model=self.model_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region=self.region_name,
        )

        self.prompt = PromptTemplate(template=CHAT_RECAP_PROMPT_TEMPLATE, input_variables=["conversation_history"])

    def generate_recap(self, chat_session: "ChatSession", messages: List["ChatMessageResponse"]) -> "ChatSessionRecap":
        """
        Generate a recap for the given chat session and messages.
        """
        try:
            conversation_history = self.format_conversation_history(messages)
            input_data = {
                "conversation_history": conversation_history,
            }

            input_message = self.prompt.invoke(input_data)
            llm_response = self.model.invoke(input_message)

            recap_data = self.parse_and_validate_response(llm_response.content)

            recap = ChatSessionRecap(
                chat_session=chat_session,
                chat_messages=[m.id for m in messages],
                recap_data=recap_data,
                status=ExecutionStatus.COMPLETED,
            )
            recap.save()

            logger.info(f"Generated recap for session {chat_session.id} with {len(messages)} messages")
            return recap

        except Exception as e:
            logger.error(f"Error generating recap for session {chat_session.id}", exc_info=True)

            recap = ChatSessionRecap(
                chat_session=chat_session,
                chat_messages=[m.id for m in messages],
                recap_data={},
                status=ExecutionStatus.FAILED,
                error_message=traceback.format_exc() + str(e),
            )
            recap.save()
            return recap

    @staticmethod
    def get_latest_recap(chat_session: "ChatSession") -> Optional["ChatSessionRecap"]:
        """
        Get the latest recap for a chat session.
        """
        try:
            recap = ChatSessionRecap.objects(chat_session=chat_session).order_by("-created_at").first()
            return recap
        except Exception as e:
            logger.error(f"Error fetching recap for session {chat_session.id}", exc_info=True)
            return None

    def format_conversation_history(self, messages: List["ChatMessageResponse"]) -> str:
        """
        Format messages into a structured conversation history.
        """
        formatted_messages = []
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            sender_info = f"{msg.sender_type}"
            if msg.sender_name:
                sender_info += f" ({msg.sender_name})"

            attachment_info = ""
            if msg.attachments:
                files = [
                    {"type": att.file_type, "name": att.file_name, "url": att.file_url}
                    for att in msg.attachments
                ]
                attachment_info = f"\nAttachments: {json.dumps(files)}"

            formatted_msg = f"[{timestamp}] {sender_info}: {msg.text}{attachment_info}"
            formatted_messages.append(formatted_msg)

        return "\n".join(formatted_messages)

    def parse_and_validate_response(self, response_content: str) -> Dict:
        """
        Parse and validate the LLM response against expected schema.
        """
        try:
            recap_data = json.loads(response_content)

            required_keys = {
                "context_of_issue",
                "conversation_highlights",
                "participants_and_roles",
                "client_sentiment",
                "communication_notes",
                "unresolved_points",
                "important_agreements_or_promises",
            }

            missing_keys = required_keys - set(recap_data.keys())
            if missing_keys:
                logger.warning(f"Missing keys in recap response: {missing_keys}")
                # Add missing keys with empty values
                for key in missing_keys:
                    recap_data[key] = [] if key in ["conversation_highlights", "unresolved_points"] else {}

            return recap_data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", exc_info=True)
            raise ValueError("Invalid JSON response from LLM") from e
