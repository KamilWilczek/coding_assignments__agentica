import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Ticket
from app.schemas import TicketResponse

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: open, in_progress, resolved"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/{ticket_id}/summary")
async def get_ticket_summary(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    client = AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    async def generate():
        try:
            # Qwen3 defaults to "thinking mode" (reasoning_content tokens before content).
            # Disable it so tokens stream directly as readable content.
            stream = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful support agent. Summarize the following help desk ticket "
                            "in 2-3 sentences. Be concise and focus on the core issue and its impact."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Title: {ticket.title}\n\nDescription: {ticket.description}",
                    },
                ],
                stream=True,
                max_tokens=300,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'content': delta.content})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
