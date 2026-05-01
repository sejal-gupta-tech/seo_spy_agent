import logging


def setup_logger():
    logger = logging.getLogger("seo_spy")

    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(formatter)

    # File handler for debugging
    file_handler = logging.FileHandler("backend_debug.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Avoid duplicate logs
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
