import socket
import random
import time
from typing import Any
from encryption.utils import send, receive


class Agent:
    """Automated agent that can be used to interact with the server for testing purposes"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.username = "User" + str(random.randint(1, 9))
        self.password = "password"
        self.receive_thread = None
        self.timeout = 5

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(self.timeout)
        self.connected = True
        if not self.connected or self.socket is None:
            raise ConnectionError("Failed to connect to the server.")

    def register(self):
        username: str = self.username
        password: str = self.password

        if not self.connected or self.socket is None:
            raise ConnectionError("Lost connection to the server.")

        self.send({"cmd": "register", "username": username, "password": password})
        response = self.receive()

        if response and response.get("response") == "ok":
            return response
        else:
            raise Exception("Failed to register")

    def login(self):
        username: str = self.username
        password: str = self.password

        if not self.connected or self.socket is None:
            raise ConnectionError("Lost connection to the server.")

        self.send({"cmd": "login", "username": username, "password": password})
        response = self.receive()

        if response and response.get("response") == "ok":
            return response
        else:
            raise Exception("Failed to login")

    def close(self) -> None:
        self.connected = False
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join()
        self.socket = None
        self.receive_thread = None

    def send(self, data_dict: dict[str, Any]) -> None:
        if not self.connected or self.socket is None:
            raise ConnectionError("Lost connection to server")

        try:
            send(self.socket, data_dict)
        except Exception as e:
            self.close()
            raise e

    def receive(self) -> dict[str, Any] | None:
        if not self.connected or self.socket is None:
            raise ConnectionError("Lost connection to server")

        try:
            return receive(self.socket)
        except Exception as e:
            self.close()
            raise e


if __name__ == "__main__":
    import os

    server_ip = os.environ.get("SERVER_IP", "127.0.0.1")
    server_port = 8888

    app = Agent(server_ip, server_port)
    app.connect()

    # Ignore registration errors, which may just mean the user is already registered
    try:
        app.register()
    except Exception as e:
        print(f"Error registering: {e}")

    try:
        app.login()
        # TODO: Event loop
        time.sleep(10)

    finally:
        app.close()
        print("Agent closed")
