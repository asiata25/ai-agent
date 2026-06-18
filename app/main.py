from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables at startup
    await init_db()
    yield

app = FastAPI(
    title="AI Chart Visualization API",
    description="Production-ready REST API App for AI Chart Visualization Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Register endpoints
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    # Start the server if file executed directly
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
