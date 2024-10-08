import logging
import queue
from logging.handlers import QueueHandler, QueueListener


def configure_logger(level: str | int = logging.INFO) -> None:
    # Configure the root logger
    root: logging.Logger = logging.getLogger()
    root.setLevel(level)

    # Create handlers
    console_handler: logging.StreamHandler = logging.StreamHandler()
    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Create a queue for sharing log messages across threads
    log_queue: queue.Queue = queue.Queue(-1)

    # Set up the queue handler
    queue_handler: QueueHandler = QueueHandler(log_queue)
    root.addHandler(queue_handler)

    # Set up the listener
    listener: QueueListener = QueueListener(log_queue, console_handler)
    listener.start()
