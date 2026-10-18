"""
Structured logging system for JARVIS.
Logs to both console and a rotating log file in the data directory.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from jarvis.core.config import DATA_DIR

LOG_FILE = DATA_DIR / "jarvis.log"


def setup_logger(name: str = "JARVIS") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Rotating file handler (5MB per file, max 3 backups)
        try:
            fh = RotatingFileHandler(
                LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"[Logger] Warning: Could not setup file handler: {e}")

    return logger


jarvis_logger = setup_logger()
