import logging
import sys

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


class RawModeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        if not msg.endswith("\r"):
            msg = msg + "\r"
        return msg


def setup_logging(raw_mode: bool = False):
    formatter_class = RawModeFormatter if raw_mode else logging.Formatter

    formatter = formatter_class(
        fmt=LOG_FORMAT,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger("RGBME").setLevel(logging.CRITICAL)
    logging.getLogger("tornado").setLevel(logging.CRITICAL)
    logging.getLogger("tornado.access").setLevel(logging.CRITICAL)
    logging.getLogger("tornado.application").setLevel(logging.CRITICAL)
    logging.getLogger("tornado.general").setLevel(logging.CRITICAL)

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logging.getLogger("tfeos")
