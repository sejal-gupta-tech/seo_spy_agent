import logging
import os


def setup_logger():
    logger = logging.getLogger("seo_spy")

    logger.setLevel(logging.INFO)
    logger.propagate = True

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

    # Ensure the root logger is also configured for console output so propagated logs appear.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_has_stream = any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
    if not root_has_stream:
        root_logger.addHandler(console_handler)

    # Attach our file handler to the seo_spy logger if root already has console output.
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers) and root_has_stream:
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()
