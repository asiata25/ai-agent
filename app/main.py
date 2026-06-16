from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agents import Agent, Runner
from agents.memory.sqlite_session import SQLiteSession
from dotenv import load_dotenv

from app.llm_models import model
from app.models import engine
from app.tools import read_csv, save_chart


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = WORKSPACE_ROOT / "example"
SESSION_ID = "chart-visualization-agent"


load_dotenv()


agent = Agent(
    "chart_visualization_assistant",
    instructions=(
        "You are a data visualization expert. When given a CSV filename from the example folder: "
        "1) call read_csv first; 2) inspect columns, types, and row count; 3) choose one best "
        "chart type from line, bar, pie, area, or horizontal bar; 4) explain your reasoning in "
        "2-3 concise sentences before generating anything; 5) call save_chart exactly once with "
        "the chosen chart type. Prefer the simplest chart that truthfully matches the data shape."
    ),
    model=model,
    tools=[read_csv, save_chart],
)


def list_example_csvs() -> list[Path]:
    if not EXAMPLE_DIR.exists():
        return []
    return sorted(EXAMPLE_DIR.glob("*.csv"))


def choose_csv_file(csv_files: list[Path]) -> Path | None:
    print("Available CSV files in example/:")
    for index, csv_file in enumerate(csv_files, start=1):
        print(f"  {index}. {csv_file.name}")

    while True:
        selection = input("Enter the number of the file you want to visualize: ").strip()
        if selection.lower() in {"exit", "quit"}:
            return None

        try:
            selected_index = int(selection)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= selected_index <= len(csv_files):
            return csv_files[selected_index - 1]

        print("Selection out of range.")


async def run_agent() -> None:
    _ = engine
    csv_files = list_example_csvs()

    if not csv_files:
        print("No CSV files found in example/.")
        return

    selected_file = choose_csv_file(csv_files)
    if selected_file is None:
        return

    session = SQLiteSession(session_id=SESSION_ID, db_path=WORKSPACE_ROOT / "database.db")
    user_prompt = (
        f"Analyze the CSV file {selected_file.name} from the example folder and generate the best chart. "
        f"Use read_csv first, explain the chart choice before generating it, then call save_chart."
    )

    print()
    runner = Runner.run_streamed(
        agent,
        input=user_prompt,
        max_turns=10,
        session=session,
    )

    async for event in runner.stream_events():
        if event.type == "raw_response_event":
            try:
                print(event.data.delta, end="", flush=True)
            except AttributeError:
                pass # ignore if delta doesn't exist
        elif event.type == "run_item_stream_event":
            if event.name == "tool_called":
                print()
                print(event.item.raw_item.name)
                print(event.item.raw_item.arguments)
            elif event.name == "tool_output":
                output = event.item.raw_item
                if isinstance(output, str):
                    print(output)
                else:
                    print(json.dumps(output, indent=2, default=str))

    print()


if __name__ == "__main__":
    asyncio.run(run_agent())
