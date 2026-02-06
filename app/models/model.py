# models.py
from pydantic import BaseModel
from typing import Optional


class UserInput(BaseModel):
    session_id: str
    message: str
    document_text: str


class Plan(BaseModel):
    task: str
    question: str


class WorkResult(BaseModel):
    answer: str
