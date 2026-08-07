import logging
import sys

import structlog


def configure_logging(level: str) -> None:
  logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, level.upper()),
  )

  structlog.configure(
    processors=[
      structlog.contextvars.merge_contextvars,
      structlog.processors.add_log_level,
      structlog.processors.TimeStamper(fmt="iso"),
      structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
    logger_factory=structlog.PrintLoggerFactory(),
  )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
  return structlog.get_logger(name)
