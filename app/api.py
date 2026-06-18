"""FastAPI endpoint for visualization agent."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.main import run_visualization
from app.models import init_db, list_visualization_history
from app.tools import normalize_chart_type, validate_csv_file


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize database on startup."""
    try:
        await init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")
    yield


app = FastAPI(
    title="Chart Visualization Agent",
    description="AI-powered CSV visualization via agent",
    version="1.0.0",
    lifespan=lifespan,
)


class VisualizationRequest(BaseModel):
    """Request schema for visualization endpoint."""

    csv_file: str = Field(..., description="Name of CSV file in example folder")
    chart_type: str | None = Field(
        None,
        description="Optional chart type: line, bar, pie, area, or horizontal bar",
    )
    session_id: str | None = Field(None, description="Optional session ID for tracking")


class VisualizationResponse(BaseModel):
    """Response schema for visualization endpoint."""

    status: str
    session_id: str
    history_id: int | None = None
    csv_file: str
    chart_type: str | None = None
    output_path: str | None = None
    message: str
    error: str | None = None


class VisualizationHistoryResponse(BaseModel):
    """Response schema for visualization history."""

    id: int
    session_id: str
    csv_file: str
    chart_type: str | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


@app.post("/visualize", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    """
    Trigger visualization for a CSV file.

    The request runs the agent and stores the result in visualization history.
    """
    csv_file = request.csv_file.strip()
    if not csv_file.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="csv_file must have .csv extension",
        )

    try:
        validate_csv_file(csv_file)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    chart_type = None
    if request.chart_type:
        try:
            chart_type = normalize_chart_type(request.chart_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    try:
        result = await run_visualization(
            csv_file=csv_file,
            chart_type=chart_type,
            session_id=request.session_id,
        )

        if result["status"] == "error":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "session_id": result.get("session_id"),
                    "history_id": result.get("history_id"),
                    "csv_file": result.get("csv_file"),
                    "chart_type": result.get("chart_type"),
                    "output_path": result.get("output_path"),
                    "message": "Visualization failed",
                    "error": result.get("error"),
                },
            )

        return VisualizationResponse(
            status="success",
            session_id=result["session_id"],
            history_id=result["history_id"],
            csv_file=result["csv_file"],
            chart_type=result.get("chart_type"),
            output_path=result.get("output_path"),
            message=f"Visualization for {csv_file} completed successfully",
            error=None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/history", response_model=list[VisualizationHistoryResponse])
async def get_history(limit: int = 20):
    """Return recent visualization runs."""
    limit = max(1, min(limit, 100))
    return await list_visualization_history(limit=limit)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
