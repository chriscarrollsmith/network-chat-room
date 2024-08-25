import os
import logging
import queue
from dotenv import load_dotenv
from logging.handlers import QueueHandler, QueueListener

load_dotenv(override=True)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def configure_logger(level: int = logging.INFO) -> None:
    # Configure the root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Create handlers
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Create a queue for sharing log messages across threads
    log_queue = queue.Queue(-1)

    # Set up the queue handler
    queue_handler = QueueHandler(log_queue)
    root.addHandler(queue_handler)

    # Set up the listener
    listener = QueueListener(log_queue, console_handler)
    listener.start()
