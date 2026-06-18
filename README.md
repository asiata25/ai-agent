# AI Chart Visualization Agent

A FastAPI-based REST API service that uses the **OpenAI Agents SDK** to autonomously visualize CSV data. The agent reads a CSV file, determines the most appropriate chart type for the dataset, explains its reasoning, and generates the chart using Matplotlib.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (for dependency management) or pip
- OpenAI API key with GPT-4.1-mini access

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```
   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Copy the example environment file and fill in your API credentials.
   ```bash
   cp .example.env .env
   ```
   Open `.env` and configure:
   ```env
   OPENAI_API_KEY=sk-your_api_key_here
   ```

## Usage

Start the API server:

```bash
uv run uvicorn app.api:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok"}
```

#### 2. Create Visualization
```bash
curl -X POST http://localhost:8000/visualize \
  -H "Content-Type: application/json" \
  -d '{"csv_file": "sales_monthly.csv"}'
```

Request body:
```json
{
  "csv_file": "sales_monthly.csv",
  "chart_type": "line",
  "session_id": "optional-custom-session-id"
}
```

Response (success):
```json
{
  "status": "success",
  "session_id": "chart-viz-a1b2c3d4",
  "history_id": 1,
  "csv_file": "sales_monthly.csv",
  "chart_type": "line",
  "output_path": "output/sales_monthly_chart.png",
  "message": "Visualization for sales_monthly.csv completed successfully",
  "error": null
}
```

Response (error):
```json
{
  "status": "error",
  "session_id": "chart-viz-a1b2c3d4",
  "history_id": 1,
  "csv_file": "sales_monthly.csv",
  "chart_type": "line",
  "output_path": null,
  "message": "Visualization failed",
  "error": "CSV file not found"
}
```

#### 3. Visualization History
```bash
curl http://localhost:8000/history
```

Response:
```json
[
  {
    "id": 1,
    "session_id": "chart-viz-a1b2c3d4",
    "csv_file": "sales_monthly.csv",
    "chart_type": "line",
    "status": "success",
    "error_message": null,
    "created_at": "2026-06-18T09:00:00",
    "completed_at": "2026-06-18T09:00:05"
  }
]
```

### Available CSV Files

The agent can visualize CSV files located in the `example/` directory:
- `employee_performance.csv`
- `population_by_country.csv`
- `product_category_share.csv`
- `sales_monthly.csv`
- `temperature_trend.csv`

## Architecture

- `app/api.py`: FastAPI application with REST endpoints.
- `app/main.py`: Core orchestration logic for visualization agent.
- `app/llm_models.py`: OpenAI model configuration with validation.
- `app/tools.py`: Agent tools (`read_csv`, `save_chart`). Matplotlib is configured with the headless `Agg` backend.
- `app/models.py`: Async SQLite database setup and schema for visualization history.

## Database

The agent maintains a SQLite database (`database.db`) that tracks visualization requests and outcomes. The database is automatically initialized on API startup.

### Schema

**visualization_history** table:
- `id`: Primary key
- `session_id`: Unique session identifier
- `csv_file`: Name of the CSV file processed
- `chart_type`: Type of chart generated
- `status`: Request status (pending, success, failed)
- `error_message`: Error details if status is failed
- `created_at`: Timestamp of request creation
- `completed_at`: Timestamp of completion

## Error Handling

The API provides clear error messages for common issues:

- **400 Bad Request**: Invalid CSV file format, unsupported chart type, or missing required fields
- **404 Not Found**: CSV file does not exist in the `example/` folder
- **500 Internal Server Error**: OpenAI API failures or runtime errors

All errors include detailed messages to aid debugging.

## Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
