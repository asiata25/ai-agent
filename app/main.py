"""Core orchestration for visualization agent."""

from __future__ import annotations

import json
import uuid

from agents import Agent, Runner
from agents.memory.sqlite_session import SQLiteSession
from dotenv import load_dotenv

from app.llm_models import get_model
from app.models import (
    DATABASE_PATH,
    create_visualization_history,
    finish_visualization_history,
    init_db,
)
from app.tools import read_csv, save_chart


load_dotenv()


def build_agent() -> Agent:
    """Build the visualization agent after runtime config is available."""
    return Agent(
        "chart_visualization_assistant",
        instructions=(
            "You are a data visualization expert. When given a CSV filename from the example folder: "
            "1) call read_csv first; 2) inspect columns, types, and row count; 3) choose one best "
            "chart type from line, bar, pie, area, or horizontal bar unless the user requests a "
            "specific compatible chart type; 4) explain your reasoning in 2-3 concise sentences "
            "before generating anything; 5) call save_chart exactly once with the chosen chart type. "
            "Prefer the simplest chart that truthfully matches the data shape."
        ),
        model=get_model(),
        tools=[read_csv, save_chart],
    )


async def run_visualization(
    csv_file: str,
    chart_type: str | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Core orchestration function for visualization.

    Args:
        csv_file: Name of CSV file in example folder
        chart_type: Optional requested chart type.
        session_id: Optional session ID. If None, generates a dynamic one.

    Returns:
        Dict with status and details of the run.
    """
    if session_id is None:
        session_id = f"chart-viz-{uuid.uuid4().hex[:8]}"

    history_id: int | None = None
    selected_chart_type = chart_type
    output_path: str | None = None

    try:
        await init_db()
        history = await create_visualization_history(
            session_id=session_id,
            csv_file=csv_file,
            chart_type=chart_type,
        )
        history_id = history.id

        session = SQLiteSession(
            session_id=session_id,
            db_path=DATABASE_PATH,
        )

        chart_instruction = (
            f"Use a {chart_type} chart if it is compatible with the data."
            if chart_type
            else "Choose the best chart type from line, bar, pie, area, or horizontal bar."
        )
        user_prompt = (
            f"Analyze the CSV file {csv_file} from the example folder and generate the best chart. "
            f"{chart_instruction} Use read_csv first, explain the chart choice before generating it, "
            f"then call save_chart."
        )

        runner = Runner.run_streamed(
            build_agent(),
            input=user_prompt,
            max_turns=10,
            session=session,
        )

        async for event in runner.stream_events():
            if event.type == "raw_response_event":
                try:
                    pass  # Suppress streaming output in API context
                except AttributeError:
                    pass
            elif event.type == "run_item_stream_event":
                item = getattr(event, "item", None)
                raw_item = getattr(item, "raw_item", None)

                if event.name == "tool_called" and getattr(raw_item, "name", None) == "save_chart":
                    try:
                        arguments = json.loads(raw_item.arguments)
                        selected_chart_type = arguments.get("chart_type") or selected_chart_type
                    except (TypeError, ValueError, AttributeError):
                        pass
                elif event.name == "tool_output":
                    output = raw_item
                    if isinstance(output, str) and output.startswith("Chart saved to: "):
                        output_path = output.removeprefix("Chart saved to: ").strip()

        await finish_visualization_history(
            history_id=history_id,
            status="success",
            chart_type=selected_chart_type,
        )

        return {
            "status": "success",
            "session_id": session_id,
            "history_id": history_id,
            "csv_file": csv_file,
            "chart_type": selected_chart_type,
            "output_path": output_path,
        }

    except Exception as e:
        if history_id is not None:
            await finish_visualization_history(
                history_id=history_id,
                status="failed",
                chart_type=selected_chart_type,
                error_message=str(e),
            )
        return {
            "status": "error",
            "session_id": session_id,
            "history_id": history_id,
            "csv_file": csv_file,
            "chart_type": selected_chart_type,
            "output_path": output_path,
            "error": str(e),
        }
