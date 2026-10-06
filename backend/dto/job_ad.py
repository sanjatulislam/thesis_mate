from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class JobAd(BaseModel):
    id: str
    headline: str = ""
    employer: str = ""
    cities: list[str] = []
    deadline_at: datetime
    posted_at: datetime
    url: str = ""
    description: str = ""