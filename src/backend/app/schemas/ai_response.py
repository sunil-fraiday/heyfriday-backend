from pydantic import BaseModel

from typing import List, Union, Dict


class Answer(BaseModel):
    answer_text: str
    answer_data: Union[List[Dict], Dict]
    answer_url: str


class Data(BaseModel):
    answer: Answer


class AIResponse(BaseModel):
    status: str
    message: str
    data: Data
