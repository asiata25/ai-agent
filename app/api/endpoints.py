from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.database import get_db
from app.db.models import VisualizationHistory
from app.services.agent_service import run_agent_visualization

router = APIRouter()

class VisualizationRequest(BaseModel):
    csv_file: str
    chart_type: str | None = None
    session_id: str | None = None

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple check to verify the service is running."""
    return {"status": "ok"}

@router.post("/visualize", status_code=status.HTTP_200_OK)
async def create_visualization(
    request: VisualizationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the agent visualization loop.
    Returns status, generated files, and choice explanations.
    """
    result = await run_agent_visualization(
        csv_file=request.csv_file,
        requested_chart_type=request.chart_type,
        session_id=request.session_id,
        db=db,
    )
    if result["status"] == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result,
        )
    return result

@router.get("/history", status_code=status.HTTP_200_OK)
async def get_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve history of all agent visualization runs."""
    query = select(VisualizationHistory).order_by(VisualizationHistory.created_at.desc()).limit(limit)
    result = await db.execute(query)
    history_records = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "csv_file": r.csv_file,
            "requested_chart_type": r.chart_type,
            "chosen_chart_type": r.chosen_chart_type,
            "output_image_path": r.output_image_path,
            "explanation": r.explanation,
            "status": r.status,
            "error_message": r.error_message,
            "created_at": r.created_at,
        }
        for r in history_records
    ]
