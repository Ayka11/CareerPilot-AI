from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field

class Job(BaseModel):
    id: Optional[int] = None
    company: str
    title: str
    url: HttpUrl
    salary: Optional[str] = None
    location: Optional[str] = None
    remote: bool = False
    part_time: bool = False
    flexible: bool = False
    description: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    source: str  # e.g., "remoteok", "remotive"
    score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied: bool = False
    hours: Optional[str] = None  # e.g., "full-time", "part-time"
