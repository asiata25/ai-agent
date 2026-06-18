from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class VisualizationHistory(Base):
    __tablename__ = "visualization_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    csv_file = Column(String, nullable=False)
    chart_type = Column(String, nullable=True)          # Requested chart type (if any)
    chosen_chart_type = Column(String, nullable=True)    # Actually chosen by agent
    output_image_path = Column(String, nullable=True)    # Path relative to workspace
    explanation = Column(String, nullable=True)          # Agent decision explanation
    status = Column(String, nullable=False)              # "SUCCESS" or "FAILED"
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
