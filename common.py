from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "creatorpilot"
    gemini_api_key: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    app_env: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
