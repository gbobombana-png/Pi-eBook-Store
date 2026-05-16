import logging
import sys
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    return logger
