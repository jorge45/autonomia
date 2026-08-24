import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
        }
        if isinstance(record.msg, dict):
            payload.update(record.msg)
        else:
            payload["mensaje"] = record.getMessage()
        return json.dumps(payload)


def configure_logging(log_level: str) -> logging.Logger:
    logger = logging.getLogger("api_propia")
    logger.setLevel(log_level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger
