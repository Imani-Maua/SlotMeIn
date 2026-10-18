import logging
import structlog


def configure_logging(level: int = logging.INFO):
    """
    Configure structlog for the application and worker.

    Outputs JSON — each log line is a machine-readable object with
    explicit fields rather than a formatted string.
    """
    logging.basicConfig(level=level, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
