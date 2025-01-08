import json
import traceback
from typing import List, Dict
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.utils.logger import get_logger
from app.schemas.chat import ChatMessageResponse
from app.models.mongodb.chat_message import ChatMessage
from app.models.mongodb.enums import ExecutionStatus
from app.models.mongodb.chat_message_analysis import ChatMessageAnalysis, AnalysisType
from .prompt import (
    INTENT_CLASSIFICATION_PROMPT_TEMPLATE,
    get_formatted_few_shot_prompts,
    CATEGORISE_CONVERSATION_PROMPT_TEMPLATE,
    category_few_shot_examples,
    few_shot_prompts,
)

logger = get_logger(__name__)


class MessageAnalysisService:
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

    def get_bedrock_model(self):
        return ChatBedrock(
            model=self.model_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region=self.region_name,
        )

    def classify_with_bedrock(
        self, current_message: str, chat_history: List[ChatMessageResponse], resource_scope_mapping: Dict
    ):
        try:
            resource_scope_mapping = json.dumps(
                {
                    "it-support": ["query"],
                    "onboarding-data": ["query"],
                    "ticket-data": ["query"],
                }
            )

            model = self.get_bedrock_model()
            examples = get_formatted_few_shot_prompts(few_shot_prompts)

            prompt = PromptTemplate(
                template=INTENT_CLASSIFICATION_PROMPT_TEMPLATE,
                input_variables=["examples", "resource_mapping", "current_message", "chat_history"],
            )

            history_string = self.format_chat_history(chat_history)
            input_data = {
                "examples": examples,
                "resource_mapping": resource_scope_mapping,
                "current_message": current_message,
                "chat_history": history_string,
            }

            input_message = prompt.invoke(input_data)
            required_resources = json.loads(model.invoke(input_message).content)

            logger.info("Required Resources:", required_resources)
        except Exception as e:
            logger.error("Error during Bedrock invocation:", exc_info=True)
            required_resources = {}

        return required_resources

    def format_chat_history(self, chat_history: List[ChatMessageResponse]):
        return "\n".join([f"{message.sender_type}: {message.text}" for message in chat_history])

    def analyse_category(self, chat_message: ChatMessage, chat_history: List[ChatMessageResponse]) -> str:
        try:
            model = self.get_bedrock_model()
            examples = get_formatted_few_shot_prompts(category_few_shot_examples)
            prompt = PromptTemplate(
                template=CATEGORISE_CONVERSATION_PROMPT_TEMPLATE,
                input_variables=["examples", "current_message", "chat_history"],
            )

            chain = prompt | model | JsonOutputParser()
            result = chain.invoke(
                {"examples": examples, "current_message": chat_message.text, "chat_history": chat_history}
            )

            ChatMessageAnalysis(
                chat_message=chat_message,
                analysis_type=AnalysisType.CATEGORY,
                status=ExecutionStatus.COMPLETED,
                analysis_data=result,
            ).save()
            return result
        except Exception as e:
            logger.error("Error during chat message analysis:", exc_info=True)
            ChatMessageAnalysis(
                chat_message_id=chat_message.id,
                analysis_type=AnalysisType.CATEGORY,
                status=ExecutionStatus.FAILED,
                analysis_data=traceback.format_exc() + str(e),
            ).save()
            return {}
