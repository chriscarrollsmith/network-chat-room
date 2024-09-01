# TODO: define authenticated command handler and
# authentication command handler dictionaries on import
# and consolidate dispatching logic in `handle` (DRY)

# Import necessary modules
import os
import socketserver
import threading
import logging
from typing import Callable
from dotenv import load_dotenv
from utils.encryption import send, receive
from utils.logger import configure_logger
from server.user_manager import UserManager
from server.chat_history import ChatHistory

load_dotenv(override=True)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Set up logger
configure_logger(LOG_LEVEL)
logger = logging.getLogger(__name__)


# RequestHandler class for managing client connections
class RequestHandler(socketserver.BaseRequestHandler):
    # Thread-safe dictionary to store connected clients
    clients: dict[str, "RequestHandler"] = {}
    clients_lock: threading.Lock = threading.Lock()

    # Load user data and chat history
    user_manager: UserManager = UserManager()
    chat_history: ChatHistory = ChatHistory()

    # Maximum buffer size for receiving data
    max_buff_size: int = 1024

    # -- Client connection lifecycle methods --

    def setup(self) -> None:
        """
        Initialize the handler for a new client connection.
        """
        self.username: str = ""
        self.file_peer: str = ""
        self.authed: bool = False
        logger.info(f"New connection from {self.client_address}")

    def handle(self) -> None:
        """
        Handle client requests and manage the client connection.
        """
        while self.request:
            try:
                # self.request is the TCP socket connected to the client
                data: dict = receive(self.request, self.max_buff_size)
                if data:
                    logger.debug(f"Received data from {self.client_address}: {data}")

                    if not self.authed:
                        self._handle_authentication(data)
                    else:
                        self._handle_authenticated_commands(data)
                else:
                    logger.error(f"Empty message received from {self.client_address}")
            except ConnectionResetError:
                logger.warning(f"Connection reset by {self.client_address}")
                break
            except ConnectionError as e:
                logger.warning(f"Connection error with {self.client_address}: {e}")
                break
            except Exception as e:
                logger.error(f"Error handling request from {self.client_address}: {e}")
                break

    def finish(self) -> None:
        """
        Clean up when a client disconnects.
        """
        logger.info(f"Client disconnected: {self.client_address}")
        if self.authed:
            self.authed = False

            with RequestHandler.clients_lock:
                if self.username in RequestHandler.clients:
                    del RequestHandler.clients[self.username]
                    logger.info(f"Removed {self.username} from connected clients")

            self._notify_peer_left()

    # -- Notification methods --

    def _notify_peer_joined(self) -> None:
        """
        Notify other clients about the new user joining.

        Triggered in `_process_login` after successful authentication.
        """
        with RequestHandler.clients_lock:
            for user in RequestHandler.clients.keys():
                send(
                    RequestHandler.clients[user].request,
                    {"type": "peer_joined", "peer": self.username},
                )

    def _notify_peer_left(self) -> None:
        """
        Notify other clients about the user leaving.

        Triggered in `finish` method after the client disconnects.
        """
        with RequestHandler.clients_lock:
            for user in RequestHandler.clients.keys():
                send(
                    RequestHandler.clients[user].request,
                    {"type": "peer_left", "peer": self.username},
                )

    # -- Command handlers --

    ## Authentication command handlers

    def _handle_authentication(self, data: dict[str, str]) -> None:
        """
        Handle authentication process for incoming connections.

        Args:
            data (dict): The received data containing authentication information.
        """
        logger.debug(f"Handling authentication for client {self.client_address}")

        if data.get("command") == "login":
            self._process_login(data)
        elif data.get("command") == "register":
            logger.debug("Received register command")
            self._process_registration(data)
        else:
            logger.warning(f"Unknown authentication command: {data.get('command')}")

    def _process_login(self, data: dict[str, str]) -> None:
        username: str = data.get("username", "")
        password: str = data.get("password", "")

        login_result: dict[str, str] = {
            "type": "login_result",
            "username": username,
        }

        if self.user_manager.validate(username, password):
            login_result.update({"response": "ok"})

            # Update authentication state
            self.username = username
            self.authed = True
            with RequestHandler.clients_lock:
                RequestHandler.clients[self.username] = self

            self._notify_peer_joined()
        else:
            login_result.update(
                {"response": "fail", "reason": "Incorrect username or password!"}
            )

        send(self.request, login_result)

    def _process_registration(self, data: dict[str, str]) -> None:
        """
        Process registration attempt.

        Args:
            data (dict): The received data containing registration information.
        """
        username: str = data.get("username", "")
        password: str = data.get("password", "")

        register_result: dict[str, str] = {
            "type": "register_result",
            "username": username,
        }

        try:
            registration_success = self.user_manager.register(username, password)

            if registration_success:
                register_result.update({"response": "ok"})
                logger.debug(f"Registration successful for user: {username}")
            else:
                register_result.update(
                    {"response": "fail", "reason": "Username already exists!"}
                )
                logger.debug(
                    f"Registration failed for user: {username} - Username already exists"
                )
        except Exception as e:
            logger.error(f"Error during registration process: {str(e)}")
            register_result.update(
                {"response": "fail", "reason": "Internal server error"}
            )
        finally:
            send(self.request, register_result)

    ## Authenticated command handlers

    def _handle_authenticated_commands(self, data: dict[str, str]) -> None:
        """
        Handle commands from authenticated users.

        Args:
            data (dict): The received data containing the command and its parameters.
        """
        command: str = data.get("command", "")

        command_handlers: dict[str, Callable[[dict[str, str]], None]] = {
            "get_users": self._handle_get_users,
            "get_history": self._handle_get_history,
            "chat": self._handle_chat,
            "file_request": self._handle_file_request,
            "file_response": self._handle_file_response,
            "close": self._handle_close,
        }

        handler = command_handlers.get(command)
        if handler:
            try:
                handler(data)
            except Exception as e:
                logger.error(
                    f"Error handling command {command} from {self.username}: {e}"
                )
        else:
            logger.warning(
                f"Unknown or missing command received from {self.username}: {command}"
            )

    def _handle_get_users(self, data: dict[str, str]) -> None:
        """
        Handle request for list of online users.

        Args:
            data (dict): The received data (unused in this method).
        """
        with RequestHandler.clients_lock:
            users = [
                user for user in RequestHandler.clients.keys() if user != self.username
            ]
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
        with RequestHandler.clients_lock:
            if data["peer"] in RequestHandler.clients:
                send(
                    RequestHandler.clients[data["peer"]].request,
                    {
                        "type": "private_message",
                        "peer": self.username,
                        "message": data["message"],
                    },
                )
        self.chat_history.append_to_history(
            self.username, data["peer"], data["message"]
        )

    def _handle_broadcast_chat(self, data: dict[str, str]) -> None:
        """
        Handle broadcast chat messages.

        Args:
            data (dict): The received data containing the broadcast chat message.
        """
        with RequestHandler.clients_lock:
            logger.debug(f"You're inside the clients lock")
            for user in RequestHandler.clients.keys():
                if user != self.username:
                    send(
                        RequestHandler.clients[user].request,
                        {
                            "type": "broadcast_message",
                            "peer": self.username,
                            "message": data["message"],
                        },
                    )
        logger.debug("You're outside the clients lock")
        self.chat_history.append_to_history(self.username, "", data["message"])

    def _handle_file_request(self, data: dict[str, str]) -> None:
        """
        Handle file transfer requests.

        Args:
            data (dict): The received data containing file transfer request information.
        """
        with RequestHandler.clients_lock:
            if data["peer"] in RequestHandler.clients:
                RequestHandler.clients[data["peer"]].file_peer = self.username
                send(
                    RequestHandler.clients[data["peer"]].request,
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
                        "type": "file_response",
                        "response": "error",
                        "reason": "Peer not found or not connected",
                    },
                )

    def _handle_file_response(self, data: dict[str, str]) -> None:
        """
        Handle file transfer responses (accept or deny).

        Args:
            data (dict): The received data containing file transfer response information.
        """
        if data["peer"] == self.file_peer:
            self.file_peer = ""
            with RequestHandler.clients_lock:
                if data["peer"] in RequestHandler.clients:
                    response = {
                        "type": "file_response",
                        "peer": self.username,
                        "response": data["response"],
                    }
                    if data["response"] == "accept":
                        response["ip"] = self.client_address[0]
                    send(RequestHandler.clients[data["peer"]].request, response)

    def _handle_close(self, data: dict[str, str]) -> None:
        """
        Handle client disconnection requests.

        Args:
            data (dict): The received data (unused in this method).
        """
        self.finish()


if __name__ == "__main__":
    try:
        load_dotenv(override=True)
        port: int = int(os.environ.get("SERVER_PORT", 8888)) or 8888

        # Start the server
        app: socketserver.ThreadingTCPServer = socketserver.ThreadingTCPServer(
            ("0.0.0.0", port), RequestHandler
        )
        logger.info(f"Server started on 0.0.0.0:{port}")
        app.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
    finally:
        if "app" in locals():
            app.server_close()
        logger.info("Server shut down")
