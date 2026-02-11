from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/invoice_rag"
    GEMINI_API_KEY: str = ""
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_EXPIRATION_DAYS: int = 7
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    model_config = {"env_file": ".env"}


settings = Settings()
