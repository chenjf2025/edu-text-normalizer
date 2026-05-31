"""日志工具"""
from loguru import logger
from app.config import config
import sys

logger.remove()
logger.add(
    sys.stdout,
    level=config.LOG.level,
    format=config.LOG.format,
    colorize=False
)
logger.add(
    "logs/app.log",
    level=config.LOG.level,
    format=config.LOG.format,
    rotation="10 MB",
    retention="7 days",
    compression="zip"
)