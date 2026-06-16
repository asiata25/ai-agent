# PRD: Assignment 4 — AI Chart Visualization Agent

## Overview

Build a terminal-based AI agent using the **OpenAI Agents SDK** that reads CSV files from an `example/` folder, presents them to the user as choices, then autonomously selects the best chart type to visualize the chosen file — explaining its reasoning — and saves the output chart to an `output/` folder.


## Objective

The agent acts as a **data visualization assistant**. It does not just write code blindly — it analyzes the structure and content of the chosen CSV file, decides which chart type best represents the data, explains why it made that choice, and then generates and saves the chart.


## Folder Structure

```
assignment_4_coding_agent/
├── app/
│   ├── main.py
│   ├── models.py
│   └── tools.py
├── example/
│   ├── sales_monthly.csv
│   ├── population_by_country.csv
│   ├── product_category_share.csv
│   ├── temperature_trend.csv
│   └── employee_performance.csv
├── output/              ← agent saves chart files here
├── tmp/workspace/       ← agent's general file sandbox
├── .env
├── .gitignore
└── requirements.txt
```

> Note: The `app/` subfolder mirrors the structure your instructor used (visible in the screenshot with `app/main.py`, `app/tools.py`). `models.py` lives alongside `main.py` inside `app/`.


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

```
$ python -m app.main

Available CSV files in example/:
  1. sales_monthly.csv
  2. population_by_country.csv
  3. product_category_share.csv
  4. temperature_trend.csv
  5. employee_performance.csv

Enter the number of the file you want to visualize: 1

[Agent thinking...]
Agent: I analyzed sales_monthly.csv. It contains time-series data with a Month
column and a Revenue column across 12 data points. I chose a LINE CHART because
the data represents a continuous trend over ordered time intervals — a line chart
best communicates the trajectory and momentum of the values.

Generating chart...
Chart saved to: output/sales_monthly_chart.png
```


## File Responsibilities

### `app/main.py`
Entry point and agent orchestrator.

- On startup, scans the `example/` folder and lists all `.csv` files
- Prompts the user to pick a file by number
- Passes the chosen filename to the agent via `Runner.run_streamed()`
- Handles `runner.stream_events()` to stream the agent's reasoning and output to the terminal
- Initializes `SQLAlchemySession` from `app/models.py` for persistent memory
- Wraps everything in `asyncio.run(run_agent())`

### `app/models.py`
Database setup only.

- Creates and exports the async SQLite engine:
  ```python
  create_async_engine("sqlite+aiosqlite:///database.db")
  ```
- Imported by `main.py` to initialize the memory session
- No agent logic lives here

### `app/tools.py`
Defines all agent tools.

**Tool 1: `read_csv(filename: str) -> str`**
- Reads the specified file from the `example/` folder
- Returns a string summary of the CSV structure: column names, data types, row count, and first 3 rows as a sample
- This is what the agent uses to analyze the data before choosing a chart type

**Tool 2: `save_chart(filename: str, chart_code: str) -> str`**
- Receives the chart-generating Python code from the agent
- Executes the code using `exec()` or writes it to `tmp/workspace/` and runs it with `subprocess`
- Saves the final chart image to `output/<filename>_chart.png`
- Returns the output path as confirmation

### `example/` folder
Contains the 5 pre-made CSV files. These are static — the agent reads but never writes to this folder.

### `output/` folder
Where all generated chart images are saved. Include a `.gitkeep` file so the folder is tracked in Git but its contents are ignored.

### `tmp/workspace/`
General sandbox for any intermediate files the agent writes. Follow the same pattern as the instructor — restrict all write operations to this path.

### `.env`
Stores `OPENAI_API_KEY`. Never committed to Git.

### `.gitignore`
Must exclude:
```
.env
database.db
output/*.png
tmp/
__pycache__/
*.pyc
.venv/
```

### `requirements.txt`
```
openai-agents
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

- [ ] Uses `openai-agents` SDK (`Agent`, `Runner`, `runner.stream_events()`) — not the basic `openai` SDK
- [ ] Persistent memory via `SQLAlchemySession` with `sqlite+aiosqlite:///database.db`
- [ ] On startup, lists all 5 CSV files from `example/` and prompts user to choose
- [ ] Agent reads the chosen CSV using the `read_csv` tool
- [ ] Agent explains its chart type choice in plain language before generating
- [ ] Agent generates the chart and saves it to `output/` using the `save_chart` tool
- [ ] Generated chart includes a title, labeled axes (where applicable), and is readable
- [ ] No files are written outside `tmp/workspace/` or `output/`
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
