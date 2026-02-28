"""
CampusShield AI — ML Service Config
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    ML_SERVICE_API_KEY: str = ""
    DEBUG: bool = False


settings = MLSettings()
