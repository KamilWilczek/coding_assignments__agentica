import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import tickets

# asyncpg requires SelectorEventLoop on Windows (ProactorEventLoop is incompatible)
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="Help Desk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
