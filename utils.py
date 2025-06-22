import logging
import hashlib
import re
from pathlib import Path
from config import Config

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(Config.LOGS_DIR / "nsi_processing.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def validate_filename(filename, pattern):
    return re.fullmatch(pattern, filename, re.IGNORECASE) is not None

def calculate_sha256(file_obj):
    hasher = hashlib.sha256()
    while chunk := file_obj.read(4096):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()