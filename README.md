# AI Chart Visualization API

A production-ready REST API App for the AI Chart Visualization Agent built using **FastAPI** and the **OpenAI Agents SDK**. The API exposes endpoints to run the agent, allowing remote systems or frontends to request chart generation, auto-detect chart types, specify a custom chart type, print live streaming thought processes directly to server console logs, and persist visualization history to a SQLite database via SQLAlchemy.

---

## Folder Architecture

The project is structured modularly:
```
app/
├── api/
│   ├── __init__.py
│   └── endpoints.py        # REST API endpoints (GET /health, POST /visualize, GET /history)
├── core/
│   ├── __init__.py
│   ├── config.py           # Configuration paths, outputs, and database URL
│   └── database.py         # SQLAlchemy engine, session maker, and schema initiator
├── db/
│   ├── __init__.py
│   └── models.py           # SQLAlchemy declarative DB model (VisualizationHistory)
├── services/
│   ├── __init__.py
│   ├── agent_service.py    # Agent runner, streaming outputs, and log compilation
│   └── tools.py            # Agent tools (@function_tool)
├── llm_models.py           # LLM Model initialization (AnyLLMModel)
└── main.py                 # FastAPI Application instance and routing setup
```

---

## Setup & Startup Instructions

### 1. Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended for dependency and workspace management)

### 2. Install Dependencies
Run the following command in the project root:
```bash
uv sync
```
*(If not using `uv`, you can run `pip install -r requirements.txt`)*

### 3. Environment Configuration
Copy the template `.env` file and fill in your API credentials:
```bash
cp .example.env .env
```
Open `.env` and fill:
```env
API_KEY=your_api_key_here
API_URL=https://your-custom-url.com
```

### 4. Start the Server
Start the development server with:
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
On startup, the app automatically initializes/verifies the SQLite database schemas in `database.db`.

---

## Interactive API Documentation (Swagger)

FastAPI automatically generates interactive API documentation. While the server is running, open your browser and navigate to:
*   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Allows you to interactively test endpoints directly in the browser)
*   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) (Clean, structured documentation view)

---

## Sequential Testing Guide

Once the server is running, perform the following tests in sequence to verify all features:

### Step 1: Health Check
Verify that the server is up and responsive:
```bash
curl -s http://127.0.0.1:8000/health
```
**Expected Response:**
```json
{"status": "ok"}
```

---

### Step 2: Auto-Visualization
Trigger the agent to analyze `sales_monthly.csv` and auto-select the best chart type:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"csv_file": "sales_monthly.csv"}' http://127.0.0.1:8000/visualize
```
- **Live Logs**: Watch the server console where the uvicorn server is running. You will see the agent's real-time thought streams, tool calls, and tool responses.
- **Output**: Verify the generated chart file at `output/sales_monthly_chart.png`.
- **Expected JSON Response**:
  ```json
  {
    "status": "SUCCESS",
    "id": 1,
    "session_id": "chart-viz-XXXXXX",
    "csv_file": "sales_monthly.csv",
    "requested_chart_type": null,
    "chosen_chart_type": "line",
    "output_image_path": "output/sales_monthly_chart.png",
    "explanation": "...[agent thought process and reasoning]..."
  }
  ```

---

### Step 3: Explicit Chart Type Request
Force the agent to generate a specific chart type (e.g. `bar` instead of the default `line` trend):
```bash
curl -X POST -H "Content-Type: application/json" -d '{"csv_file": "sales_monthly.csv", "chart_type": "bar"}' http://127.0.0.1:8000/visualize
```
- **Output**: Verify that the generated chart at `output/sales_monthly_chart.png` is updated to a bar chart.
- **Expected JSON Response**: Shows `"requested_chart_type": "bar"` and `"chosen_chart_type": "bar"`.

---

### Step 4: Verify Run History
Query the database logging history to make sure the previous visualization runs are properly persisted:
```bash
curl -s http://127.0.0.1:8000/history
```
**Expected Response:**
A JSON list containing records of all past runs with detailed metadata, including session ID, chart parameters, output paths, and explanations.

---

### Step 5: Test Error Handling
Test how the app handles requesting a file that does not exist:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"csv_file": "non_existent.csv"}' http://127.0.0.1:8000/visualize
```
- **Result**: The agent receives the error from the `read_csv` tool and outputs a natural response stating that the file was not found. The run is logged in the history database with `status: SUCCESS` but `chosen_chart_type: null`.
