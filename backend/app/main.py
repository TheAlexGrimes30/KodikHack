from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.rag_api import router as rag_router
from backend.app.workflow_api import router as workflow_router
from backend.db.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""

    yield
    await engine.dispose()

app = FastAPI( title="BussinesAI",
               description="AI assistant for business ideas",
               version="1.0.0",
               lifespan=lifespan
             )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)
app.include_router(workflow_router)

@app.get("/")
async def root():
    """Return the application status message."""

    return {"message": "Backend is running"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
