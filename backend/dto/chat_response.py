from pydantic import BaseModel

class ChatResponse(BaseModel):
    reply: str
    thread_id: str