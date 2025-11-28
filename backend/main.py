from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from database import create_db_tables
from routers import meetings, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    os.makedirs("uploads", exist_ok=True)
    yield


app = FastAPI(
    title="AI Meeting Summarizer",
    description="Upload audio/video → transcript, summary, action items, speaker separation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])
app.include_router(search.router,   prefix="/api/search",   tags=["search"])


@app.get("/")
def root():
    return {"status": "ok", "service": "AI Meeting Summarizer"}
