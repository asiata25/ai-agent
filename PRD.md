# PRD: Assignment 4 — AI Chart Visualization Agent

## Overview

Build a FastAPI-based AI agent service using the **OpenAI Agents SDK** that accepts CSV visualization requests over HTTP, reads CSV files from an `example/` folder, autonomously selects or validates the chart type, explains its reasoning internally through the agent workflow, saves the output chart to an `output/` folder, and records request history in SQLite.


## Objective

The agent acts as a **data visualization assistant**. It does not just write code blindly — it analyzes the structure and content of the chosen CSV file, decides which chart type best represents the data, explains why it made that choice, and then generates and saves the chart.


## Folder Structure

```
assignment_4_coding_agent/
├── app/
│   ├── api.py
│   ├── main.py
│   ├── models.py
│   ├── tools.py
│   └── llm_models.py
├── .env
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

> Note: This PRD follows the instructor-style layout shown in the screenshots. The `app/` folder contains the main entrypoint, model setup, tool definitions, and model configuration side by side.


## Example CSV Files

Each file should have clear, distinct data shapes so the agent can meaningfully differentiate between chart types.

| File | Content | Expected Best Chart |
|---|---|---|
| `sales_monthly.csv` | Month, Revenue columns (12 rows) | Line chart — shows trend over time |
| `population_by_country.csv` | Country, Population columns (10 rows) | Bar chart — compares discrete categories |
| `product_category_share.csv` | Category, Percentage columns (5–6 rows) | Pie chart — shows part-to-whole composition |
| `temperature_trend.csv` | Date, Min Temp, Max Temp columns (30 rows) | Area chart — shows range/band over time |
| `employee_performance.csv` | Employee, Score, Department columns (15 rows) | Horizontal bar chart — ranked comparison across named entities |


## User Flow

```bash
uv run uvicorn app.api:app --reload

curl -X POST http://localhost:8000/visualize \
  -H "Content-Type: application/json" \
  -d '{"csv_file": "sales_monthly.csv"}'
```


## File Responsibilities

### `app/main.py`
Entry point and agent orchestrator.

- Imports the configured model from `app/llm_models.py`
- Creates the `Agent` and wires in the tools from `app/tools.py`
- Streams the agent response with `Runner.run_streamed()`
- Keeps the terminal loop in `asyncio.run(run_agent())`

### `app/models.py`
Database setup only.

- Creates and exports the async SQLite engine with:
  ```python
  create_async_engine("sqlite+aiosqlite:///database.db")
  ```
- Imported by `main.py` for persistent storage
- No agent logic lives here

### `app/tools.py`
Defines all agent tools.

- Contains the instructor-style function tools, including file write/edit helpers and a shell command executor
- Restricts file operations to the workspace path used by the agent
- Uses `@function_tool` so the agent can call the tools directly

### `app/llm_models.py`
Model configuration only.

- Holds the model object or model name used by the agent
- Keeps provider-specific setup out of `main.py`

### `.env`
Stores `OPENAI_API_KEY`. Never committed to Git.

### `.gitignore`
Must exclude:
```
.env
database.db
__pycache__/
*.pyc
.venv/
```

### `requirements.txt`
```
openai-agents
fastapi
uvicorn[standard]
pydantic
sqlmodel
sqlalchemy
aiosqlite
greenlet
python-dotenv
matplotlib
pandas
```


## Agent Behavior Specification

### System Prompt (suggested)
```
You are a data visualization expert. When given a CSV filename:
1. Use the read_csv tool to inspect the file's structure and data.
2. Analyze the columns, data types, and number of rows.
3. Choose the single best chart type (line, bar, pie, area, or horizontal bar)
   to represent the data. Think about: is it time-series? categorical comparison?
   part-to-whole? ranked entities?
4. Explain your reasoning clearly in 2–3 sentences before generating anything.
5. Use the save_chart tool to generate and save the chart using matplotlib.
   Always label axes, add a title, and use a clean visual style.
```

### Chart Decision Logic (agent should reason through this)
| Data shape | Best chart |
|---|---|
| One column is a date/time sequence | Line chart |
| Comparing values across named categories | Bar chart |
| Values sum to ~100% (proportions) | Pie chart |
| Two numeric columns over time (range) | Area chart |
| Named entities ranked by a score | Horizontal bar chart |

---

## Acceptance Criteria

- [ ] Uses the instructor-style `app/main.py`, `app/models.py`, `app/tools.py`, and `app/llm_models.py` layout
- [ ] Persistent memory uses `sqlite+aiosqlite:///database.db`
- [ ] Agent tools are defined in `app/tools.py` with `@function_tool`
- [ ] Model setup stays isolated in `app/llm_models.py`
- [ ] No files are written outside the workspace path used by the tools
- [ ] `.env` and `database.db` are excluded from the GitHub repo via `.gitignore`
- [ ] Code is pushed to a public GitHub repository

---

## What You Do NOT Need to Build

- A web UI or REST API — terminal only
- Real-time code execution in a true sandbox (optional, not required)
- Support for user-uploaded CSVs — the 5 example files are fixed
- Multiple chart outputs per session — one file, one chart per run


## Critical Notes

> **SDK trap:** `from openai import OpenAI` is the wrong import. You need `from agents import Agent, Runner`. These are different packages entirely — using the wrong one causes point deductions.

> **Async driver:** Your database URL must be `sqlite+aiosqlite:///database.db`, not `sqlite:///database.db`. The `aiosqlite` suffix is required for async compatibility.

> **Agent reasoning is mandatory:** The agent must output its chart-type rationale as text before calling `save_chart`. Do not skip this step — it is core to the assignment's coding agent behavior and shows the agent is making an informed decision, not just guessing.
