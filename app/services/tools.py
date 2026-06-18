from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from agents import function_tool

from app.core.settings import settings


def _resolve_workspace_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = settings.workspace_root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(settings.workspace_root)
    except ValueError as exc:
        raise ValueError(f"Path must stay inside the workspace: {path}") from exc

    return resolved


def _resolve_example_csv(file_name: str) -> Path:
    candidate = _resolve_workspace_path(Path("example") / file_name)
    if candidate.parent != settings.example_dir:
        raise ValueError("CSV files must come from the example/ folder")
    if candidate.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are supported")
    if not candidate.exists():
        raise FileNotFoundError(f"CSV file not found: {file_name}")
    return candidate


def _clean_chart_type(chart_type: str) -> str:
    normalized = chart_type.strip().lower().replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    aliases = {
        "horizontalbar": "horizontal bar",
        "horizontal bar chart": "horizontal bar",
        "h bar": "horizontal bar",
        "hbar": "horizontal bar",
    }
    return aliases.get(normalized, normalized)


def _prepare_dataframe(file_name: str) -> pd.DataFrame:
    file_path = _resolve_example_csv(file_name)
    return pd.read_csv(file_path)


def _summarize_dataframe(file_name: str, dataframe: pd.DataFrame) -> str:
    datetime_columns: list[str] = []
    numeric_columns: list[str] = []

    for column in dataframe.columns:
        if pd.api.types.is_numeric_dtype(dataframe[column]):
            numeric_columns.append(column)
            continue

        parsed = pd.to_datetime(dataframe[column], errors="coerce")
        if parsed.notna().mean() >= 0.8:
            datetime_columns.append(column)

    summary: dict[str, Any] = {
        "file": file_name,
        "rows": int(len(dataframe)),
        "columns": list(dataframe.columns),
        "dtypes": {column: str(dtype) for column, dtype in dataframe.dtypes.items()},
        "numeric_columns": numeric_columns,
        "datetime_columns": datetime_columns,
        "preview": dataframe.head(8).to_dict(orient="records"),
    }

    if numeric_columns:
        summary["numeric_summary"] = dataframe[numeric_columns].describe().round(3).to_dict()

    return json.dumps(summary, indent=2, default=str)


def _pick_category_column(dataframe: pd.DataFrame) -> str:
    for column in dataframe.columns:
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            return column
    return dataframe.columns[0]


def _pick_numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    return [column for column in dataframe.columns if pd.api.types.is_numeric_dtype(dataframe[column])]


def _pick_time_column(dataframe: pd.DataFrame) -> str:
    for column in dataframe.columns:
        parsed = pd.to_datetime(dataframe[column], errors="coerce")
        if parsed.notna().mean() >= 0.8:
            return column
    return dataframe.columns[0]


def _format_title(file_name: str, chart_type: str) -> str:
    stem = Path(file_name).stem.replace("_", " ").title()
    return f"{stem} - {chart_type.title()} Chart"


def inspect_csv(file_name: str) -> str:
    """Inspect a CSV file from the example folder."""
    dataframe = _prepare_dataframe(file_name)
    return _summarize_dataframe(file_name, dataframe)


def generate_chart(file_name: str, chart_type: str) -> str:
    """Generate and save a chart for a CSV file from the example folder."""
    dataframe = _prepare_dataframe(file_name)
    chart_type = _clean_chart_type(chart_type)
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    output_path = settings.output_dir / f"{Path(file_name).stem}_chart.png"
    title = _format_title(file_name, chart_type)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    category_column = _pick_category_column(dataframe)
    numeric_columns = _pick_numeric_columns(dataframe)
    time_column = _pick_time_column(dataframe)

    if chart_type == "pie":
        if not numeric_columns:
            raise ValueError("Pie charts require at least one numeric column")
        value_column = numeric_columns[0]
        values = dataframe[value_column]
        labels = dataframe[category_column]
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(title)

    elif chart_type == "bar":
        if not numeric_columns:
            raise ValueError("Bar charts require at least one numeric column")
        value_column = numeric_columns[0]
        ax.bar(dataframe[category_column].astype(str), dataframe[value_column], color="#2c7be5")
        ax.set_xlabel(category_column)
        ax.set_ylabel(value_column)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=45)

    elif chart_type == "horizontal bar":
        if not numeric_columns:
            raise ValueError("Horizontal bar charts require at least one numeric column")
        value_column = numeric_columns[0]
        ordered = dataframe.sort_values(value_column, ascending=True)
        ax.barh(ordered[category_column].astype(str), ordered[value_column], color="#00a3a3")
        ax.set_xlabel(value_column)
        ax.set_ylabel(category_column)
        ax.set_title(title)

    elif chart_type == "area":
        if len(numeric_columns) >= 2:
            x_values = pd.to_datetime(dataframe[time_column], errors="coerce")
            if x_values.notna().sum() < max(2, len(dataframe) // 2):
                x_values = dataframe[time_column]
            lower_column, upper_column = numeric_columns[:2]
            ax.plot(x_values, dataframe[lower_column], color="#1f77b4", linewidth=2)
            ax.plot(x_values, dataframe[upper_column], color="#ff7f0e", linewidth=2)
            ax.fill_between(
                x_values,
                dataframe[lower_column],
                dataframe[upper_column],
                color="#4c78a8",
                alpha=0.25,
            )
            ax.set_xlabel(time_column)
            ax.set_ylabel("Value")
        elif numeric_columns:
            x_values = pd.to_datetime(dataframe[time_column], errors="coerce")
            if x_values.notna().sum() < max(2, len(dataframe) // 2):
                x_values = dataframe[time_column]
            value_column = numeric_columns[0]
            ax.fill_between(x_values, dataframe[value_column], color="#4c78a8", alpha=0.35)
            ax.plot(x_values, dataframe[value_column], color="#1f77b4", linewidth=2)
            ax.set_xlabel(time_column)
            ax.set_ylabel(value_column)
        else:
            raise ValueError("Area charts require numeric data")
        ax.set_title(title)

    else:
        if not numeric_columns:
            raise ValueError("Line charts require at least one numeric column")

        x_values = pd.to_datetime(dataframe[time_column], errors="coerce")
        if x_values.notna().sum() < max(2, len(dataframe) // 2):
            x_values = dataframe[time_column]

        for column in numeric_columns:
            ax.plot(x_values, dataframe[column], marker="o", linewidth=2, label=column)

        ax.set_xlabel(time_column)
        ax.set_ylabel("Value")
        ax.set_title(title)
        if len(numeric_columns) > 1:
            ax.legend()

    fig.tight_layout()
    fig.autofmt_xdate()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return f"Chart saved to: {output_path.relative_to(settings.workspace_root)}"


@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a file inside the workspace."""
    file_path = _resolve_workspace_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"Wrote {file_path.relative_to(settings.workspace_root)}"


@function_tool
def edit_file(path: str, old: str, new: str) -> str:
    """Replace text in a file inside the workspace."""
    file_path = _resolve_workspace_path(path)
    content = file_path.read_text(encoding="utf-8")

    if old not in content:
        return f"Text not found in {file_path.relative_to(settings.workspace_root)}"

    file_path.write_text(content.replace(old, new), encoding="utf-8")
    return f"Edited {file_path.relative_to(settings.workspace_root)}"


@function_tool
def exec_command(command: str) -> str:
    """Run a shell command from the workspace root."""
    completed = subprocess.run(
        command,
        shell=True,
        cwd=settings.workspace_root,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return output.strip() or "Command completed"


@function_tool
def read_csv(file_name: str) -> str:
    """Inspect a CSV file from the example folder."""
    return inspect_csv(file_name)


@function_tool
def save_chart(file_name: str, chart_type: str) -> str:
    """Generate and save a chart for a CSV file from the example folder."""
    return generate_chart(file_name, chart_type)
