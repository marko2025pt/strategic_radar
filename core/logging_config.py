# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
# core/logging_config.py
# Centralised logging configuration for Strategic Radar.
# Import get_logger() in every module — never configure logging elsewhere.
#
# Usage:
#   from core.logging_config import get_logger
#   logger = get_logger(__name__)
#   logger.info("Something happened")
#   logger.error("Something failed", exc_info=True)

import logging
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

# Project root — two levels up from core/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# Log format
# ─────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ─────────────────────────────────────────────
# Root logger configuration
# ─────────────────────────────────────────────

def _configure_root_logger():
    """
    Configures the root logger once.
    - Daily rotating log file: logs/YYYY-MM-DD.log
    - Console output for development
    - Called automatically on first import
    """
    root_logger = logging.getLogger()

    # Avoid adding handlers multiple times if module is re-imported
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler — daily log file ──
    log_filename = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ── Console handler — INFO and above ──
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # ── Silence noisy third party loggers ──
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai._base_client").setLevel(logging.WARNING)
    logging.getLogger("openai._streaming").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain_openai").setLevel(logging.WARNING)

# Configure on import
_configure_root_logger()

# ─────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger for a module.

    Usage:
        from core.logging_config import get_logger
        logger = get_logger(__name__)

    The __name__ variable automatically resolves to the module path
    e.g. 'rag.retriever', 'agent.nodes', 'agent.tools.tavily'
    """
    return logging.getLogger(name)