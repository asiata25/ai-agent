from pydantic import BaseModel

class VisualizationRequest(BaseModel):
    csv_file: str
    chart_type: str | None = None
    session_id: str | None = None
