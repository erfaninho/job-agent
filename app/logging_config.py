import logging

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    settings.logs_path.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=settings.app_log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
