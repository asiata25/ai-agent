import json
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from agents import Agent, Runner
from agents.memory.sqlite_session import SQLiteSession

from app.llm_models import model
from app.core.settings import settings
from app.db.models import VisualizationHistory
from app.services.tools import read_csv, save_chart

# Configure agent
agent = Agent(
    "chart_visualization_assistant",
    instructions=(
        "You are a data visualization expert. When given a CSV filename from the example folder:\n"
        "1) call read_csv first;\n"
        "2) inspect columns, types, and row count;\n"
        "3) choose one best chart type from line, bar, pie, area, or horizontal bar;\n"
        "4) explain your reasoning in 2-3 concise sentences before generating anything;\n"
        "5) call save_chart exactly once with the chosen chart type. Prefer the simplest chart that truthfully matches the data shape.\n"
        "If a specific chart type is requested by the user, please select that chart type."
    ),
    model=model,
    tools=[read_csv, save_chart],
)

async def run_agent_visualization(
    csv_file: str,
    requested_chart_type: str | None,
    session_id: str | None,
    db: AsyncSession,
) -> dict:
    """
    Run the chart visualization agent, streaming logs to the console,
    saving history to the database, and handling errors.
    """
    # 1. Enforce/generate dynamic session ID if none was passed
    if not session_id:
        session_id = f"chart-viz-{uuid.uuid4().hex[:8]}"

    # Resolve CSV file and construct prompt
    csv_path = Path(csv_file)
    csv_name = csv_path.name
    
    user_prompt = (
        f"Analyze the CSV file {csv_name} from the example folder and generate the chart. "
        f"Use read_csv first, explain the chart choice before generating it, then call save_chart."
    )
    if requested_chart_type:
        user_prompt += f" The user has explicitly requested a '{requested_chart_type}' chart type. Please use this chart type."

    print(f"\n--- Starting Visualization Run [Session: {session_id}] ---", flush=True)
    print(f"CSV file: {csv_name}", flush=True)
    if requested_chart_type:
        print(f"Requested Chart Type: {requested_chart_type}", flush=True)
    print(f"Prompt sent: {user_prompt}\n", flush=True)

    session = SQLiteSession(session_id=session_id, db_path=settings.db_path)
    explanation_parts = []
    chosen_chart_type = None

    try:
        runner = Runner.run_streamed(
            agent,
            input=user_prompt,
            max_turns=10,
            session=session,
        )

        async for event in runner.stream_events():
            if event.type == "raw_response_event":
                try:
                    delta = event.data.delta
                    explanation_parts.append(delta)
                    print(delta, end="", flush=True)
                except AttributeError:
                    pass
            elif event.type == "run_item_stream_event":
                if event.name == "tool_called":
                    tool_name = event.item.raw_item.name
                    arguments = event.item.raw_item.arguments
                    print(f"\n[Tool Call] {tool_name} with arguments: {arguments}", flush=True)
                    
                    if tool_name == "save_chart":
                        # Attempt to parse arguments
                        args = arguments
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                pass
                        if isinstance(args, dict):
                            chosen_chart_type = args.get("chart_type")

                elif event.name == "tool_output":
                    output = event.item.raw_item
                    print(f"\n[Tool Output]", flush=True)
                    if isinstance(output, str):
                        print(output, flush=True)
                    else:
                        print(json.dumps(output, indent=2, default=str), flush=True)

        print(f"\n--- Run Completed [Session: {session_id}] ---\n", flush=True)

        explanation = "".join(explanation_parts).strip()
        stem = Path(csv_name).stem
        output_image_path = f"output/{stem}_chart.png"

        # Record visualization run history
        from sqlalchemy.future import select
        stmt = select(VisualizationHistory).where(VisualizationHistory.session_id == session_id)
        res = await db.execute(stmt)
        history = res.scalar_one_or_none()

        if history:
            history.chosen_chart_type = chosen_chart_type or (requested_chart_type or "unknown")
            history.output_image_path = output_image_path
            history.explanation = explanation
            history.status = "SUCCESS"
            history.error_message = None
        else:
            history = VisualizationHistory(
                session_id=session_id,
                csv_file=csv_name,
                chart_type=requested_chart_type,
                chosen_chart_type=chosen_chart_type or (requested_chart_type or "unknown"),
                output_image_path=output_image_path,
                explanation=explanation,
                status="SUCCESS",
                error_message=None,
            )
            db.add(history)
        await db.commit()
        if history.id is None:
            await db.refresh(history)

        return {
            "status": "SUCCESS",
            "id": history.id,
            "session_id": session_id,
            "csv_file": csv_name,
            "requested_chart_type": requested_chart_type,
            "chosen_chart_type": chosen_chart_type,
            "output_image_path": output_image_path,
            "explanation": explanation,
        }

    except Exception as e:
        print(f"\n[Error] Failed to run agent: {e}", flush=True)
        
        # Save failure to DB
        from sqlalchemy.future import select
        stmt = select(VisualizationHistory).where(VisualizationHistory.session_id == session_id)
        res = await db.execute(stmt)
        history = res.scalar_one_or_none()

        if history:
            history.status = "FAILED"
            history.error_message = str(e)
        else:
            history = VisualizationHistory(
                session_id=session_id,
                csv_file=csv_name,
                chart_type=requested_chart_type,
                chosen_chart_type=None,
                output_image_path=None,
                explanation=None,
                status="FAILED",
                error_message=str(e),
            )
            db.add(history)
        await db.commit()
        
        return {
            "status": "FAILED",
            "session_id": session_id,
            "csv_file": csv_name,
            "error_message": str(e),
        }
