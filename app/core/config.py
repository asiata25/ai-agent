from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Workspace paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = WORKSPACE_ROOT / "example"
OUTPUT_DIR = WORKSPACE_ROOT / "output"

# Database path and connection URL
DB_PATH = WORKSPACE_ROOT / "database.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
