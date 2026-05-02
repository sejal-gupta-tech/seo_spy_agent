import logging
import os


def setup_logger():
    logger = logging.getLogger("seo_spy")

    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(formatter)

    # File handler for debugging (only if NOT on Vercel)
    is_vercel = os.getenv("VERCEL") == "1"
    
    if not is_vercel:
        try:
            file_handler = logging.FileHandler("backend_debug.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            if not logger.handlers:
                logger.addHandler(file_handler)
        except Exception:
            # Fallback if filesystem is read-only elsewhere
            pass

    # Avoid duplicate logs for console
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()
