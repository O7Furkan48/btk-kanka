from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://kanka:kanka_dev@localhost:5432/kanka"

    google_api_key: str = ""

    vllm_base_url: str = "http://192.168.35.24:8001/v1"

    chroma_dir: str = "./app/data/chroma"
    model_dir: str = "./app/data/models"
    raw_dir: str = "../data-collection/raw"

    chroma_http_url: str = ""

    env: str = "development"

    @property
    def is_dev(self) -> bool:
        return self.env == "development"

settings = Settings()
