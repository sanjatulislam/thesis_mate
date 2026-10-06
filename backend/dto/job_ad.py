from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class JobAd(BaseModel):
    id: str
    headline: str = ""
    employer: str = ""
    cities: list[str] = []
    deadline_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    url: str = ""
    description: str = ""