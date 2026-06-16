# AI Chart Visualization Agent

A terminal-based AI agent built using the **OpenAI Agents SDK** that autonomously visualizes CSV data. The agent reads a CSV file, determines the most appropriate chart type for the dataset, explains its reasoning, and then generates the chart using Matplotlib.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (for dependency management)

## Setup

1. **Install dependencies:**
   The project uses `uv` for lightning-fast package management.
   ```bash
   uv sync
   ```

2. **Environment Variables:**
   Copy the example environment file and fill in your API credentials.
   ```bash
   cp .example.env .env
   ```
   Open `.env` and configure:
   ```env
   API_KEY=your_api_key_here
   API_URL=https://your-custom-url.com
   ```

## Usage

Run the agent interactively using:

```bash
uv run python -m app.main
```

You will be presented with a list of example CSV files. Enter the number corresponding to the file you wish to visualize. 

The agent will:
1. Load and read the CSV.
2. Analyze the columns, rows, and data types.
3. Stream its thought process, concluding with the optimal chart type (e.g., Pie Chart, Horizontal Bar, Line Chart).
4. Save the generated chart to the `output/` directory.

## Architecture

- `app/main.py`: Entry point. Wires up the agent, reads example files, and handles the streaming output.
- `app/llm_models.py`: Model configuration, currently configured for `AnyLLMModel`.
- `app/tools.py`: Agent tools (`read_csv`, `save_chart`). Matplotlib is explicitly configured to use the headless `Agg` backend for seamless background generation.
- `app/models.py`: Async SQLite database setup for agent memory.

## Example Output

```text
Available CSV files in example/:
  1. employee_performance.csv
  2. population_by_country.csv
  3. product_category_share.csv
  4. sales_monthly.csv
  5. temperature_trend.csv
Enter the number of the file you want to visualize: 3

...
Agent: The best chart type for this data would be a pie chart because the data represents parts of a whole (market share percentages that sum to 100%).
Chart Choice: Pie Chart
...
```
