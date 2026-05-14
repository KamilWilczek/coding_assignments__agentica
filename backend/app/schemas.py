from datetime import datetime
from pydantic import BaseModel


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
