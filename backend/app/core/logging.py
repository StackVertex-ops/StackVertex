"""Structured Logging Configuration.

JSON-formatted logging for CloudWatch, Sentry, and local development.
"""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context fields."""

    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        """Add custom fields to log record.

        Args:
            log_record: Dictionary that will be JSON-encoded
            record: Python LogRecord
            message_dict: Dictionary from parse() call
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record, self.datefmt)

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add extra fields (from logger.info("msg", extra={...}))
        for key, value in message_dict.items():
            if key not in log_record:
                log_record[key] = value


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    enable_cloudwatch: bool = False,
    enable_sentry: bool = False,
    sentry_dsn: str | None = None,
    environment: str = "development",
) -> None:
    """Setup application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting (True for production)
        enable_cloudwatch: Send logs to AWS CloudWatch
        enable_sentry: Enable Sentry error tracking
        sentry_dsn: Sentry DSN URL
        environment: Environment name (development, staging, production)
    """
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        # JSON format for production (CloudWatch, log aggregation)
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # CloudWatch Handler (optional)
    if enable_cloudwatch:
        try:
            import watchtower

            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group_name="/stackvertex/backend",
                stream_name=f"{environment}-api",
                use_queues=True,  # Async logging
                send_interval=10,  # Batch every 10 seconds
            )
            cloudwatch_handler.setLevel(logging.INFO)
            cloudwatch_handler.setFormatter(formatter)
            root_logger.addHandler(cloudwatch_handler)

            root_logger.info("CloudWatch logging enabled")

        except ImportError:
            root_logger.warning(
                "CloudWatch logging requested but 'watchtower' not installed. "
                "Install with: pip install watchtower"
            )
        except Exception as e:
            root_logger.warning(f"Failed to setup CloudWatch logging: {e}")

    # Sentry Error Tracking (optional)
    if enable_sentry and sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration

            # Configure Sentry
            sentry_logging = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )

            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                integrations=[sentry_logging],
                traces_sample_rate=0.1 if environment == "production" else 1.0,
                profiles_sample_rate=0.1 if environment == "production" else 1.0,
                send_default_pii=False,  # Don't send PII (GDPR compliance)
            )

            root_logger.info("Sentry error tracking enabled")

        except ImportError:
            root_logger.warning(
                "Sentry tracking requested but 'sentry-sdk' not installed. "
                "Install with: pip install sentry-sdk"
            )
        except Exception as e:
            root_logger.warning(f"Failed to setup Sentry: {e}")

    # Suppress noisy third-party loggers
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={
            "level": level,
            "json_format": json_format,
            "cloudwatch": enable_cloudwatch,
            "sentry": enable_sentry,
            "environment": environment,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
