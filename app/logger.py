import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a configured logger that logs to app.log."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    log_dir = Path(__file__).resolve().parent.parent
    log_file = log_dir / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
