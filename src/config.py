"""Configuration loader with environment variable support."""
from __future__ import annotations
import os
from pathlib import Path
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseConfig(BaseSettings):
    """Database configuration."""
    model_config = SettingsConfigDict(extra="ignore")
    host: str = "localhost"
    port: int = 5432
    name: str = "test_db"
    password: str = Field(default="", description="Loaded from env var APP_DATABASE__PASSWORD")

class HttpConfig(BaseSettings):
    """HTTP client settings."""
    model_config = SettingsConfigDict(extra="ignore")
    base_url: str = "https://api.example.com"
    timeout: int = 30
    retry_count: int = 3   

class AppConfig(BaseSettings):
    """Application metadata."""
    model_config = SettingsConfigDict(extra="ignore")
    name: str = "my-test-framework"
    version: str = "0.1.0"

class Settings(BaseSettings):
    """Root configuration container."""
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_nested_delimiter="__",   # APP_DATABASE__HOST → settings.database.host
        extra="ignore",              # 忽略未知字段
    )
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    http: HttpConfig = HttpConfig()
    api_key: str = Field(default="", description="Loaded from env var APP_API_KEY")

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """Load settings from YAML file, then apply env vars."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        # YAML 数据作为默认值，环境变量可以覆盖
        return cls(**yaml_data)
    

def load_settings(env: str="dev") -> Settings:
    """Load settings for specific environment."""
    base_path = Path("configs/base.yaml")
    env_path = Path(f"configs/{env}.yaml")

    # 先加载 base
    settings = Settings.from_yaml(base_path)

    # 再加载环境配置（覆盖 base）
    if env_path.exists():
        with open(env_path, "r") as f:
            env_data = yaml.safe_load(f)

        # 合并：env 覆盖 base
        settings = Settings(**{**settings.model_dump(), **env_data})
    return settings