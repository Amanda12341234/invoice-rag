from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.services.vector_store import init_vector_store
from app.api.v1 import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    init_vector_store()
    yield


app = FastAPI(title="AI 智能發票管家 API", lifespan=lifespan)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
