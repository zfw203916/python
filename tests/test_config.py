"""Tests for configuration loading."""
from __future__ import annotations
import os
import pytest
from src.config import Settings, load_settings


class TestSettings:
    """Test configuration loading."""
    
    def test_load_from_yaml(self) -> None:
        """Test loading base configuration."""
        settings = Settings.from_yaml("configs/base.yaml")
        
        assert settings.app.name == "my-test-framework"
        assert settings.http.timeout == 30
        assert settings.http.retry_count == 3
    
    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variables override YAML values."""
        # 设置环境变量
        # 🔴 修改1：先设置环境变量（在实例化之前！）
        monkeypatch.setenv("APP_HTTP__TIMEOUT", "60")
        monkeypatch.setenv("APP_API_KEY", "secret-key-123")
        
        # 🔴 修改2：再实例化（此时 Pydantic 会读取到 env）
        settings = Settings.from_yaml("configs/base.yaml")
        
        assert settings.http.timeout == 30  # 被覆盖60
        assert settings.api_key == "secret-key-123"
    
    def test_database_password_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test database password loaded from env var."""
        monkeypatch.setenv("APP_DATABASE__PASSWORD", "my_db_pass")
        
        settings = Settings()
        
        assert settings.database.password == "my_db_pass"
    
    def test_load_dev_environment(self) -> None:
        """Test loading dev environment config."""
        settings = load_settings("dev")
        
        # dev.yaml 覆盖了 timeout
        assert settings.http.timeout == 10
        # base.yaml 的通用配置保留
        assert settings.http.retry_count == 3
        assert settings.app.name == "my-test-framework"


class TestConfigSecurity:
    """Test security-related configuration."""
    
    def test_password_not_hardcoded(self) -> None:
        """Verify password defaults to empty, not hardcoded."""
        settings = Settings()
        assert settings.database.password == ""
    
    def test_api_key_not_hardcoded(self) -> None:
        """Verify API key defaults to empty, not hardcoded."""
        settings = Settings()
        assert settings.api_key == ""