import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str = (
        "mongodb+srv://bhushananokar2023comp_db_user:mongo@cluster0.hs9v1d8.mongodb.net/"
    )
    DATABASE_NAME: str = "qa_gen_db"  # Connect to qa_gen_spice database
    QUESTIONS_COLLECTION: str = "dsa_questions"  # Questions collection from qa_gen_spice

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"

    # Docker Configuration
    DOCKER_TIMEOUT: int = 30  # seconds
    DOCKER_MEMORY_LIMIT: str = "256m"
    DOCKER_CPU_QUOTA: int = 50000  # 0.5 CPU
    CONTAINER_TTL: int = 300  # 5 minutes

    # Application Configuration
    API_TITLE: str = "Sandbox Environment API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
