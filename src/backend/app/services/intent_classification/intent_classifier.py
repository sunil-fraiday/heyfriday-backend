import json
from typing import List, Dict

from app.utils.logger import get_logger
from app.schemas.chat import ChatMessageResponse
from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from .prompt import INTENT_CLASSIFICATION_PROMPT_TEMPLATE, get_formatted_few_shot_prompts

logger = get_logger(__name__)


class IntentClassificationService:
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

    def classify_with_bedrock(
        self, current_message: str, chat_history: List[ChatMessageResponse], resource_scope_mapping: Dict
    ):
        try:
            resource_scope_mapping = json.dumps(
                {
                    "TicketData": ["query"],
                    "RevenueData": ["query"],
                    "SalesData": ["query"],
                    "ITSupport": ["query"],
                }
            )

            model = ChatBedrock(
                model=self.model_name,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region=self.region_name,
            )

            examples = get_formatted_few_shot_prompts()

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
