from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

  secret_key: SecretStr
  algorithm: str = "HS256"
  access_token_expires_minutes: int = 30

settings = Settings()

