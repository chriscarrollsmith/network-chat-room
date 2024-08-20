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
        self.socket: socket.socket | None = None
        self.host: str = host
        self.port: int = port
        self.connected: bool = False
        self.username: str = ""
        self.receive_thread: threading.Thread | None = None
        self.max_buff_size: int = 1024
        self.event_handlers: dict[str, list[Callable]] = {
            "unknown": [lambda data: logger.debug(f"Ignored unhandled event: {data}")]
        }

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.start_receive_loop()

            self.validate_connection_state(should_be_connected=True)
        except Exception as e:
            logger.error(f"Failed to connect to server: {str(e)}")
            raise ConnectionError(f"Failed to connect to server: {str(e)}")

    def validate_connection_state(self, should_be_connected: bool = True) -> None:
        state: str = "connected" if should_be_connected else "disconnected"
        opposite_state: str = "disconnected" if should_be_connected else "connected"

        if should_be_connected != self.connected:
            raise ConnectionError(f"Expected to be {state} but was {opposite_state}.")

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
        if not self.connected or self.socket is None:
            raise ConnectionError("Error sending data: lost connection to server")
        try:
            send(self.socket, data_dict)
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            self.close_connection()
            raise e

    def receive(self) -> dict[str, Any] | None:
        if not self.connected or self.socket is None:
            raise ConnectionError("Not connected to server")
        try:
            data: dict[str, Any] = receive(self.socket, self.max_buff_size)
            return data
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
            return None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            self.close_connection()
            return None
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            self.close_connection()
            return None

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
        self.event_handlers = {
            "unknown": [lambda data: logger.debug(f"Ignored unhandled event: {data}")]
        }

    def _receive_loop(self) -> None:
        while self.connected:
            data: dict | None = self.receive()
            if data:
                event: str = data.get("type", "unknown")
                handlers: list[Callable] = self.event_handlers.get(event, [])
                for handler in handlers:
                    handler(data)
            else:
                logger.warning(f"Empty message received from server.")

    def close_connection(self) -> None:
        self.connected = False
        if self.socket:
            self.socket.close()
        self.socket = None
        self.close_receive_thread()

    def close_receive_thread(self) -> None:
        if self.receive_thread and self.receive_thread != threading.current_thread():
            # Wait for the receive loop to finish
            self.receive_thread.join()
        self.receive_thread = None
