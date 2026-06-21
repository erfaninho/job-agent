from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Application Manager"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    storage_path: Path = Field(
        default=Path("storage"),
        validation_alias=AliasChoices("STORAGE_DIR", "JOBAGENT_STORAGE_PATH"),
    )
    database_url: str = Field(
        default="sqlite:///storage/job_agent.db",
        validation_alias=AliasChoices("DATABASE_URL", "JOBAGENT_DATABASE_URL"),
    )
    model_provider: str = Field(
        default="ollama", validation_alias=AliasChoices("MODEL_PROVIDER", "JOBAGENT_MODEL_PROVIDER")
    )
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", validation_alias="OPENAI_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5-coder:3b", validation_alias="OLLAMA_MODEL")
    lmstudio_base_url: str = Field(default="http://localhost:1234/v1", validation_alias="LMSTUDIO_BASE_URL")
    lmstudio_model: str = Field(default="", validation_alias="LMSTUDIO_MODEL")
    model_name: str = Field(
        default="qwen2.5-coder:3b", validation_alias=AliasChoices("MODEL_NAME", "JOBAGENT_MODEL_NAME")
    )
    latex_compiler: str = Field(default="tectonic", validation_alias="JOBAGENT_LATEX_COMPILER")
    browser_headless: bool = Field(default=False, validation_alias="BROWSER_HEADLESS")
    require_manual_submit: bool = Field(default=True, validation_alias="REQUIRE_MANUAL_SUBMIT")

    applications_dir: Path | None = Field(default=None, validation_alias="APPLICATIONS_DIR")
    profile_dir: Path | None = Field(default=None, validation_alias="PROFILE_DIR")
    master_cv_dir: Path | None = Field(default=None, validation_alias="MASTER_CV_DIR")

    @property
    def master_cv_path(self) -> Path:
        return self.master_cv_base_path / "master_cv.tex"

    @property
    def master_cv_pdf_path(self) -> Path:
        return self.master_cv_base_path / "master_cv.pdf"

    @property
    def master_cv_base_path(self) -> Path:
        return self.master_cv_dir or self.storage_path / "master_cv"

    @property
    def profile_base_path(self) -> Path:
        return self.profile_dir or self.storage_path / "profile"

    @property
    def profile_path(self) -> Path:
        return self.profile_base_path / "profile.json"

    @property
    def answer_bank_path(self) -> Path:
        return self.profile_base_path / "answer_bank.json"

    @property
    def facts_path(self) -> Path:
        return self.profile_base_path / "facts.json"

    @property
    def preferences_path(self) -> Path:
        return self.profile_base_path / "preferences.json"

    @property
    def links_path(self) -> Path:
        return self.profile_base_path / "links.json"

    @property
    def documents_path(self) -> Path:
        return self.profile_base_path / "documents.json"

    @property
    def sensitive_answers_example_path(self) -> Path:
        return self.profile_base_path / "sensitive_answers.json.example"

    @property
    def applications_path(self) -> Path:
        return self.applications_dir or self.storage_path / "applications"

    @property
    def logs_path(self) -> Path:
        return self.storage_path / "logs"

    @property
    def app_log_path(self) -> Path:
        return self.logs_path / "app.log"

    @property
    def selected_model(self) -> str:
        if self.model_provider == "openai":
            return self.openai_model
        if self.model_provider == "lmstudio":
            return self.lmstudio_model
        if self.model_provider == "ollama":
            return self.ollama_model
        return self.model_name

    def required_folders(self) -> list[Path]:
        return [
            self.storage_path,
            self.applications_path,
            self.profile_base_path,
            self.master_cv_base_path,
            self.master_cv_base_path / "assets" / "images",
            self.master_cv_base_path / "assets" / "icons",
            self.master_cv_base_path / "assets" / "fonts",
            self.logs_path,
        ]

    def validate_model_settings(self) -> list[str]:
        errors: list[str] = []
        if self.model_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when MODEL_PROVIDER=openai.")
        if self.model_provider == "ollama" and not self.ollama_model:
            errors.append("OLLAMA_MODEL is required when MODEL_PROVIDER=ollama.")
        if self.model_provider == "lmstudio" and not self.lmstudio_model:
            errors.append("LMSTUDIO_MODEL is required when MODEL_PROVIDER=lmstudio.")
        return errors


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings()
