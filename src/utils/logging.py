import logging

# Create a custom logger
logger = logging.getLogger(__name__)


def setup_logging(log_file="app.log", level=logging.INFO):
    logging.basicConfig(
        filename=log_file, filemode="a", format="%(asctime)s - %(levelname)s - %(message)s", level=level
    )


def log_info(message):
    logger.info(message)


def log_warning(message):
    logger.warning(message)


def log_error(message):
    logger.error(message)


def log_debug(message):
    logger.debug(message)
