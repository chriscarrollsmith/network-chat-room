# Import necessary modules
import socketserver
import logging
from typing import Callable
from encryption.utils import send, receive
from server.user_manager import UserManager
from server.chat_history import ChatHistory
import threading

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Handler class for managing client connections
class Handler(socketserver.BaseRequestHandler):
    # Thread-safe dictionary to store connected clients
    clients: dict[str, "Handler"] = {}
    clients_lock: threading.Lock = threading.Lock()

    # Load user data and chat history
    user_manager: UserManager = UserManager()
    chat_history: ChatHistory = ChatHistory()

    # Maximum buffer size for receiving data
    max_buff_size: int = 1024

    def setup(self) -> None:
        """
        Initialize the handler for a new client connection.
        """
        self.username: str = ""
        self.file_peer: str = ""
        self.authed: bool = False
        logging.info(f"New connection from {self.client_address}")

    def handle(self) -> None:
        """
        Handle client requests and manage the client connection.
        """
        try:
            while True:
                try:
                    data: dict = receive(self.request, self.max_buff_size)
                    logging.debug(f"Received data from {self.client_address}: {data}")

                    if not self.authed:
                        self._handle_authentication(data)
                    else:
                        self._handle_authenticated_commands(data)
                except ConnectionResetError:
                    logging.warning(f"Connection reset by {self.client_address}")
                    break
                except ConnectionError as e:
                    logging.warning(f"Connection error with {self.client_address}: {e}")
                    break
                except Exception as e:
                    logging.error(
                        f"Error handling request from {self.client_address}: {e}"
                    )
                    break
        finally:
            self.finish()

    def finish(self) -> None:
        """
        Clean up when a client disconnects.
        """
        logging.info(f"Client disconnected: {self.client_address}")
        if self.authed:
            self.authed = False

            with Handler.clients_lock:
                if self.username in Handler.clients:
                    del Handler.clients[self.username]
                    logging.info(f"Removed {self.username} from connected clients")

            self._notify_peer_left()

    def _handle_authentication(self, data: dict[str, str]) -> None:
        """
        Handle authentication process for incoming connections.

        Args:
            data (dict): The received data containing authentication information.
        """
        self.username = data.get("username", "")

        if data.get("cmd") == "login":
            self._process_login(data)
        elif data.get("cmd") == "register":
            self._process_registration(data)

    def _process_login(self, data: dict[str, str]) -> None:
        if self.user_manager.validate(
            data.get("username", ""), data.get("password", "")
        ):
            send(self.request, {"response": "ok"})
            self.authed = True
            with Handler.clients_lock:
                Handler.clients[self.username] = self
            self._notify_peer_joined()
        else:
            send(
                self.request,
                {
                    "response": "fail",
                    "reason": "Incorrect username or password!",
                },
            )

    def _process_registration(self, data: dict[str, str]) -> None:
        """
        Process registration attempt.

        Args:
            data (dict): The received data containing registration information.
        """
        if self.user_manager.register(
            data.get("username", ""), data.get("password", "")
        ):
            send(self.request, {"response": "ok"})
        else:
            send(
                self.request,
                {"response": "fail", "reason": "Username already exists!"},
            )

    def _notify_peer_joined(self) -> None:
        """
        Notify other clients about the new user joining.
        """
        with Handler.clients_lock:
            for user in Handler.clients.keys():
                send(
                    Handler.clients[user].request,
                    {"type": "peer_joined", "peer": self.username},
                )

    def _handle_authenticated_commands(self, data: dict[str, str]) -> None:
        """
        Handle commands from authenticated users.

        Args:
            data (dict): The received data containing the command and its parameters.
        """
        cmd_handlers: dict[str, Callable[[dict[str, str]], None]] = {
            "get_users": self._handle_get_users,
            "get_history": self._handle_get_history,
            "chat": self._handle_chat,
            "file_request": self._handle_file_request,
            "file_deny": self._handle_file_deny,
            "file_accept": self._handle_file_accept,
            "close": self._handle_close,
        }

        command: str = data.get("cmd", "")
        handler = cmd_handlers.get(command)
        if handler:
            try:
                handler(data)
            except Exception as e:
                logging.error(
                    f"Error handling command {command} from {self.username}: {e}"
                )
        else:
            logging.warning(
                f"Unknown or missing command received from {self.username}: {command}"
            )

    def _handle_get_users(self, data: dict[str, str]) -> None:
        """
        Handle request for list of online users.

        Args:
            data (dict): The received data (unused in this method).
        """
        with Handler.clients_lock:
            users = [user for user in Handler.clients.keys() if user != self.username]
        send(self.request, {"type": "get_users", "data": users})

    def _handle_get_history(self, data: dict[str, str]) -> None:
        """
        Handle request for chat history.

        Args:
            data (dict): The received data containing the peer for which history is requested.
        """
        send(
            self.request,
            {
                "type": "get_history",
                "peer": data["peer"],
                "data": self.chat_history.get_history(self.username, data["peer"]),
            },
        )

    def _handle_chat(self, data: dict[str, str]) -> None:
        """
        Handle chat messages (both private and broadcast).

        Args:
            data (dict): The received data containing the chat message and its recipient.
        """
        if data["peer"] != "":
            self._handle_private_chat(data)
        else:
            self._handle_broadcast_chat(data)

    def _handle_private_chat(self, data: dict[str, str]) -> None:
        """
        Handle private chat messages.

        Args:
            data (dict): The received data containing the private chat message and its recipient.
        """
        with Handler.clients_lock:
            if data["peer"] in Handler.clients:
                send(
                    Handler.clients[data["peer"]].request,
                    {"type": "msg", "peer": self.username, "msg": data["msg"]},
                )
        self.chat_history.append_to_history(self.username, data["peer"], data["msg"])

    def _handle_broadcast_chat(self, data: dict[str, str]) -> None:
        """
        Handle broadcast chat messages.

        Args:
            data (dict): The received data containing the broadcast chat message.
        """
        with Handler.clients_lock:
            for user in Handler.clients.keys():
                if user != self.username:
                    send(
                        Handler.clients[user].request,
                        {
                            "type": "broadcast",
                            "peer": self.username,
                            "msg": data["msg"],
                        },
                    )
        self.chat_history.append_to_history(self.username, "", data["msg"])

    # TODO: Use a different key (e.g., "status") for success/failure, not a separate error event type
    def _handle_file_request(self, data: dict[str, str]) -> None:
        """
        Handle file transfer requests.

        Args:
            data (dict): The received data containing file transfer request information.
        """
        with Handler.clients_lock:
            if data["peer"] in Handler.clients:
                Handler.clients[data["peer"]].file_peer = self.username
                send(
                    Handler.clients[data["peer"]].request,
                    {
                        "type": "file_request",
                        "peer": self.username,
                        "filename": data["filename"],
                        "size": data["size"],
                        "md5": data["md5"],
                    },
                )
            else:
                send(
                    self.request,
                    {
                        "type": "file_request_error",
                        "reason": "Peer not found or not connected",
                    },
                )

    def _handle_file_deny(self, data: dict[str, str]) -> None:
        """
        Handle file transfer denials.

        Args:
            data (dict): The received data containing file transfer denial information.
        """
        if data["peer"] == self.file_peer:
            self.file_peer = ""
            with Handler.clients_lock:
                if data["peer"] in Handler.clients:
                    send(
                        Handler.clients[data["peer"]].request,
                        {"type": "file_deny", "peer": self.username},
                    )

    def _handle_file_accept(self, data: dict[str, str]) -> None:
        """
        Handle file transfer acceptances.

        Args:
            data (dict): The received data containing file transfer acceptance information.
        """
        if data["peer"] == self.file_peer:
            self.file_peer = ""
            with Handler.clients_lock:
                if data["peer"] in Handler.clients:
                    send(
                        Handler.clients[data["peer"]].request,
                        {"type": "file_accept", "ip": self.client_address[0]},
                    )

    def _handle_close(self, data: dict[str, str]) -> None:
        """
        Handle client disconnection requests.

        Args:
            data (dict): The received data (unused in this method).
        """
        self.finish()

    def _notify_peer_left(self) -> None:
        """
        Notify other clients about the user leaving.
        """
        with Handler.clients_lock:
            for user in Handler.clients.keys():
                send(
                    Handler.clients[user].request,
                    {"type": "peer_left", "peer": self.username},
                )


if __name__ == "__main__":

    try:
        # Start the server
        app: socketserver.ThreadingTCPServer = socketserver.ThreadingTCPServer(
            ("0.0.0.0", 8888), Handler
        )
        logging.info("Server started on 0.0.0.0:8888")
        app.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")
    finally:
        if "app" in locals():
            app.server_close()
        logging.info("Server shut down")
