from pydantic import BaseModel
from typing import Optional
from agents.state import PlanStep

class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    program: Optional[str] = None
    steps: list[PlanStep] = []