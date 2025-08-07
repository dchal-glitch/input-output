from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Generic Response Schemas
class Message(BaseModel):
    message: str


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
