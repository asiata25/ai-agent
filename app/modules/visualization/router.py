import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.settings import settings
from app.db.models import VisualizationHistory
from .schema import VisualizationRequest
from .tasks import run_visualization_task

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple check to verify the service is running."""
    return {"status": "ok"}

@router.post("/visualize", status_code=status.HTTP_202_ACCEPTED)
async def create_visualization(
    request: VisualizationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the agent visualization loop in the background.
    Returns immediately with task information.
    """
    # Safe check if CSV file exists in example/
    exists = False
    try:
        candidate = settings.workspace_root / "example" / request.csv_file
        resolved = candidate.resolve()
        # Ensure it resolves to a path inside example_dir, is a file, and has .csv suffix
        resolved.relative_to(settings.example_dir)
        if resolved.exists() and resolved.is_file() and resolved.suffix.lower() == ".csv":
            exists = True
    except Exception:
        pass

    session_id = request.session_id or f"chart-viz-{uuid.uuid4().hex[:8]}"

    if not exists:
        # File does not exist, log to DB and return immediately to prevent token waste
        history = VisualizationHistory(
            session_id=session_id,
            csv_file=request.csv_file,
            chart_type=request.chart_type,
            status="FAILED",
            error_message=f"CSV file not found: {request.csv_file}",
        )
        db.add(history)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "FAILED",
                "session_id": session_id,
                "csv_file": request.csv_file,
                "error_message": f"CSV file not found: {request.csv_file}",
            }
        )

    # Pre-create history record with PENDING status
    history = VisualizationHistory(
        session_id=session_id,
        csv_file=request.csv_file,
        chart_type=request.chart_type,
        status="PENDING",
    )
    db.add(history)
    await db.commit()

    # Enqueue background task
    payload = request.model_dump(mode="json")
    payload["session_id"] = session_id  # Ensure the session_id is carried forward
    run_visualization_task.delay(payload)

    return {
        "message": "Visualization job created successfully",
        "session_id": session_id,
        "status": "PENDING",
    }

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
