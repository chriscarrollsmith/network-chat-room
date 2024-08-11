import time
from client.network_manager import NetworkManager
from typing import Callable


class ChatManager:
    """
    Manages chat-related operations, including sending and receiving messages,
    and handling user selections.
    """

    def __init__(self, network_manager: NetworkManager):
        """
        Initialize the ChatManager with network and UI managers.

        Args:
            network_manager (NetworkManager): Handles network communications.
        """
        self.network_manager: NetworkManager = network_manager
        # Peer username or chat room name
        self.current_session: str = ""

    def send_message(
        self, message: str, callback: Callable[[str, str, str], None]
    ) -> None:
        """
        Send a chat message to the current session.

        Args:
            message (str): The message to be sent.
            callback (Callable[[str, str, str], None]): A callback function
                (append_message) to update the UI.
        """
        # Ignore empty messages
        if not message.strip():
            return

        # Generate timestamp for the message
        timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # Send the message to the server
        self.network_manager.send(
            {"cmd": "chat", "peer": self.current_session, "message": message}
        )

        # Update the UI with the sent message
        callback("You", timestamp, message)
