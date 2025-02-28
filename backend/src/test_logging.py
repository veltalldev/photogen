from core.logging_config import setup_logging
import logging

# Setup logging
logger = setup_logging()

def test_logging():
    logger.debug("This is a debug message - shouldn't show up")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test exception logging
    try:
        1/0
    except Exception as e:
        logger.exception("This is an exception with traceback")

if __name__ == "__main__":
    test_logging() 