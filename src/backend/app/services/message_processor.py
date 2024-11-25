import re
import requests
import traceback
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.schemas.message import MessageResponse


class MessageProcessor:
    def __init__(self, db: Session):
        self.db = db
    
    def get_text_to_sql(self, message: str) -> str:
        try:
            response = requests.post(
                settings.TEXT_TO_SQL_SERVICE_URL,
                params={"question": message},
            )
            sql_response = response.json()
            return sql_response["sql"]
        except Exception as e:
            logging.error(f"Error in text_to_sql: {str(e)}")
            logging.error(traceback.format_exc())
            raise Exception("Error in text_to_sql")

    def execute_query(self, message: str) -> MessageResponse:
        try:
            query = self.get_text_to_sql(message)
            result = self.db.execute(text(query))
            data = [dict(row) for row in result.mappings().all()]

            return MessageResponse(message="Here is the result for your question", sql_data=data)

        except Exception as e:
            logging.error(str(e) + traceback.format_exc())
            return MessageResponse(message=f"Error executing query: {str(e)}", data=None)
