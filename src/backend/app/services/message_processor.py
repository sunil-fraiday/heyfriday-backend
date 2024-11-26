import re
import requests
import traceback
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.schemas.ai_response import AIResponse


class MessageProcessor:

    def get_response(self, message: str) -> AIResponse:
        try:
            response = requests.post(
                settings.AI_SERVICE_URL,
                params={"question": message},
            )
            ai_response = response.json()
            return AIResponse(**ai_response)
        except Exception as e:
            logging.error(f"Error in ai service: {str(e)}")
            logging.error(traceback.format_exc())
            raise Exception("Error in AI Service")
