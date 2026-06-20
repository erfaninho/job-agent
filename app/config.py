from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Application Manager"
    storage_path: Path = Field(default=Path("storage"), validation_alias="JOBAGENT_STORAGE_PATH")
    database_url: str = Field(
        default="sqlite:///storage/jobagent.db", validation_alias="JOBAGENT_DATABASE_URL"
    )
    model_provider: str = Field(default="local", validation_alias="JOBAGENT_MODEL_PROVIDER")
    model_name: str = Field(default="local-rules", validation_alias="JOBAGENT_MODEL_NAME")
    latex_compiler: str = Field(default="tectonic", validation_alias="JOBAGENT_LATEX_COMPILER")

    @property
    def master_cv_path(self) -> Path:
        return self.storage_path / "master_cv" / "master_cv.tex"

    @property
    def profile_path(self) -> Path:
        return self.storage_path / "profile" / "profile.json"

    @property
    def answer_bank_path(self) -> Path:
        return self.storage_path / "profile" / "answer_bank.json"

    @property
    def applications_path(self) -> Path:
        return self.storage_path / "applications"


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings()
