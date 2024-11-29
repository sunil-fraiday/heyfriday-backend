import boto3
import json

from app.utils.logger import get_logger

logger = get_logger(__name__)


class IntentClassificationService:
    def __init__(
        self,
        aws_runtime: str,
        region_name: str,
        access_key_id: str,
        secret_access_key: str,
        model_name: str,
        resource_scope_mapping: dict,
    ):
        self.aws_runtime = aws_runtime
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.model_name = model_name
        self.resource_scope_mapping = resource_scope_mapping

    def classify_with_bedrock(self, messages, resource_scope_mapping):
        prompt = (
            "You are an intent classifier. Your job is to analyze a set of messages and infer the resources "
            "and scopes required to handle those messages. Resources represent datasets or entities, and scopes "
            "represent the operations that can be performed on those resources. Given the following inputs:\n\n"
            "Available Resources and Scopes:\n"
            f"{json.dumps(resource_scope_mapping, indent=4)}\n\n"
            "Messages:\n"
        )

        for i, message in enumerate(messages):
            prompt += f"{i + 1}. {message['content']}\n"

        prompt += (
            "\nFor each message, identify the resources and the scopes required to handle it. "
            "The response should be in the format of a JSON where the keys are resource names, "
            "and the values are lists of scopes. The output should be strictly in JSON only dont include anything other than the response\n\n"
            "Example Output:\n"
            "{\n"
            "    'TicketData': ['query'],\n"
            "    'AccountData': ['query'],\n"
            "    'SalesData': ['query']\n"
            "}\n\n"
            "Now, analyze the messages and provide the output."
        )

        bedrock_client = boto3.client(
            self.aws_runtime,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

        try:
            response = bedrock_client.invoke_model(
                modelId=self.model_name,
                accept="application/json",
                contentType="application/json",
                body=json.dumps({"prompt": prompt}),
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))
            logger.debug("Response Body from Bedrock:", response_body)

            required_resources = json.loads(response_body["outputs"][0]["text"])
            logger.info("Required Resources:", required_resources)
        except Exception as e:
            logger.error("Error during Bedrock invocation:", exc_info=True)
            required_resources = {}

        return required_resources
