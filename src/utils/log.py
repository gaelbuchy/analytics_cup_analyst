import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # Also print to console
    ]
)


def log_message(message):
    logger = logging.getLogger(__name__)
    logger.info(message)
