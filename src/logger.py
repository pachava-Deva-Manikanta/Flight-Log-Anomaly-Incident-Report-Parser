import logging
import os


def get_logger(name):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger(name)

    # Add handlers only once (avoids duplicate log lines)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger