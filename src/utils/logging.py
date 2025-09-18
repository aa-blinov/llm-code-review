import sys
from pathlib import Path

from loguru import logger


def setup_logging(level="INFO"):
    """
    Настройка логирования с помощью loguru.
    Логи пишутся в консоль и в файл с ротацией.
    """
    logger.remove()

    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="5 MB",
        retention="10 days",
        compression="zip",
        encoding="utf-8",
    )

    return logger


def get_logger():
    """Получить настроенный logger"""
    return logger


def log_info(message):
    logger.info(message)


def log_warning(message):
    logger.warning(message)


def log_error(message):
    logger.error(message)


def log_debug(message):
    logger.debug(message)


setup_logging()
