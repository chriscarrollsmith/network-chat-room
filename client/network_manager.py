import socket
import json
import threading
import logging
from typing import Any, Callable
from encryption.utils import send, receive

logger = logging.getLogger(__name__)


class NetworkManager:
    def __init__(self, host: str, port: int):
        self.socket: socket.socket | None = None
        self.host: str = host
        self.port: int = port
        self.connected: bool = False
        self.receive_thread: threading.Thread | None = None
        self.max_buff_size: int = 1024
        self.event_handlers: dict[str, list[Callable]] = {}

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
        return self.connected

    def send(self, data_dict: dict[str, Any]) -> None:
        if not self.connected or self.socket is None:
            raise ConnectionError("Not connected to server")
        try:
            send(self.socket, data_dict)
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            self.close()

    def receive(self) -> dict[str, Any] | None:
        if not self.connected or self.socket is None:
            raise ConnectionError("Not connected to server")
        try:
            return receive(self.socket, self.max_buff_size)
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
            return None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            self.close()
            return None
        except Exception as e:
            logger.error(f"Receive error: {str(e)}")
            self.close()
            return None

    def login(self, username: str, password: str) -> dict | None:
        self.send({"cmd": "login", "user": username, "pwd": password})
        response = self.receive()
        if response and response.get("response") == "ok":
            self.username = username
            self.start_receive_loop()
        return response

    def register(self, username: str, password: str) -> bool:
        self.send({"cmd": "register", "user": username, "pwd": password})
        response = self.receive()
        return True if response and response.get("response") == "ok" else False

    def start_receive_loop(self) -> None:
        if not self.receive_thread:
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.start()

    def add_event_handler(self, event: str, handler: Callable) -> None:
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def _receive_loop(self) -> None:
        while self.connected:
            data: dict | None = self.receive()
            if data:
                event: str = data.get("cmd", "unknown")
                handlers: list[Callable] = self.event_handlers.get(event, [])
                for handler in handlers:
                    handler(data)

    def close(self) -> None:
        self.connected = False
        if self.socket:
            self.socket.close()
        if self.receive_thread and self.receive_thread != threading.current_thread():
            self.receive_thread.join()
        self.socket = None
        self.receive_thread = None
