from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AI Chart Visualization API"
    redis_url: str = "redis://localhost:6379/0"
    api_key: str
    api_url: str
    
    # Workspace paths
    workspace_root: Path = Path(__file__).resolve().parents[2]
    
    @property
    def example_dir(self) -> Path:
        return self.workspace_root / "example"
        
    @property
    def output_dir(self) -> Path:
        return self.workspace_root / "output"
        
    @property
    def db_path(self) -> Path:
        return self.workspace_root / "database.db"
        
    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
