import socket
import json
import threading
import logging
import time
from typing import Any, Callable
from utils.encryption import send, receive

logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.socket: socket.socket | None = None
        self.max_buff_size: int = 1024
        self.receive_thread: threading.Thread | None = None

        self.username: str = ""
        self.event_handlers: dict[str, list[Callable]] = {}

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.start_receive_loop()

            self.validate_connection_state(should_be_connected=True)
        except Exception as e:
            logger.error(f"Failed to connect to server: {str(e)}")
            raise ConnectionError(f"Failed to connect to server: {str(e)}")

    def validate_connection_state(self, should_be_connected: bool = True) -> None:
        if should_be_connected:
            if not self.socket:
                raise ConnectionError(
                    f"Expected socket to exist but it was {self.socket}."
                )
            if not self.receive_thread:
                raise ConnectionError(
                    f"Expected receive thread to exist but it was {self.receive_thread}."
                )

            # Wait for the thread to become alive with a 1-second timeout
            start_time: float = time.time()
            timeout: float = 5.0
            logger.debug(
                f"Waiting for receive thread to become alive (timeout: {timeout}s)..."
            )
            while not self.receive_thread.is_alive():
                if time.time() - start_time > timeout:
                    raise ConnectionError(
                        f"Receive thread failed to start within {timeout}-second timeout."
                    )
                time.sleep(0.01)
            logger.debug(f"Receive thread is alive.")
        else:
            if self.socket:
                raise ConnectionError(
                    f"Expected socket to be None but it was {self.socket}."
                )
            if self.receive_thread and self.receive_thread.is_alive():
                raise ConnectionError(
                    f"Expected receive thread to not be alive but it was."
                )

    def send(self, data_dict: dict[str, Any]) -> None:
        try:
            if not self.socket:
                raise ConnectionError("Lost connection to server")
            send(self.socket, data_dict)
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            self.close_connection()
            raise e

    def start_receive_loop(self) -> None:
        if not self.receive_thread:
            self.receive_thread = threading.Thread(
                target=self._receive_loop, daemon=True
            )
            self.receive_thread.start()

    def add_event_handler(self, event: str, handler: Callable) -> None:
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def clear_event_handlers(self) -> None:
        self.event_handlers = {}

    def handle_receive_errors(self, receive_func: Callable) -> dict[str, Any] | None:
        try:
            if not self.socket:
                raise ConnectionError("Not connected to server")
            data: dict[str, Any] = receive_func(self.socket, self.max_buff_size)
            logger.debug(f"Decrypted data: {data}")
            return data
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
            return None
        except TimeoutError as e:
            logger.error("Receive timed out: {e}")
            self.close_connection()
            return None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            self.close_connection()
            return None
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            self.close_connection()
            return None

    def _receive_loop(self) -> None:
        while self.socket:
            data: dict | None = self.handle_receive_errors(receive)
            if data:
                event: str = data.get("type", "unknown")
                handlers: list[Callable] = self.event_handlers.get(event, [])
                if not handlers:
                    logger.debug(f"Ignored unhandled event: {data}")
                else:
                    for handler in handlers:
                        handler(data)
            else:
                logger.warning(f"Empty message received from server.")

    def close_connection(self) -> None:
        if self.socket:
            self.socket.close()
        self.socket = None
        self.close_receive_thread()

    def close_receive_thread(self) -> None:
        if self.receive_thread and self.receive_thread != threading.current_thread():
            # Wait for the receive loop to finish
            self.receive_thread.join()
        self.receive_thread = None
