import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "botconvenios.log"

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("botconvenios")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=5_000_000, backupCount=5)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
