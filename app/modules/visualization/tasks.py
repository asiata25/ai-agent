import asyncio
from app.worker import celery_app
from .schema import VisualizationRequest
from app.services.agent_service import run_agent_visualization
from app.core.database import AsyncSessionLocal

@celery_app.task
def run_visualization_task(payload: dict):
    # Reconstruct validation schema inside task worker
    request = VisualizationRequest(**payload)
    
    async def execute():
        async with AsyncSessionLocal() as db:
            result = await run_agent_visualization(
                csv_file=request.csv_file,
                requested_chart_type=request.chart_type,
                session_id=request.session_id,
                db=db,
            )
            return result

    # Run the async function synchronously using asyncio.run
    return asyncio.run(execute())
