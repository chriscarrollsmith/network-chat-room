import os
import pickle
import time
import logging
from dotenv import load_dotenv
from pathlib import Path
from threading import Lock

load_dotenv()

# Ensure that the data directory exists
STORAGE_DIR: Path = Path.cwd() / os.getenv("STORAGE_DIR", ".ncr-data")
STORAGE_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


class ChatHistory:
    def __init__(self) -> None:
        self.lock = Lock()
        self.history_filepath: Path = STORAGE_DIR / "history.dat"
        self.history: dict[tuple[str, str], list[tuple[str, str, str]]] = (
            self.load_history()
        )

        # Log absolute path of history file
        logger.debug(f"History file path: {self.history_filepath.absolute()}")

    def get_chat_identifier(self, u1: str, u2: str) -> tuple[str, str]:
        """
        Get a unique identifier for a conversation between two users.

        Args:
            u1: First username.
            u2: Second username.

        Returns:
            A tuple containing the two usernames, ordered to ensure consistency.
        """
        return (u1, u2) if (u2, u1) not in self.history.keys() else (u2, u1)

    def append_to_history(self, sender: str, receiver: str, msg: str) -> None:
        """
        Append a message to the chat history.

        Args:
            sender: The username of the message sender.
            receiver: The username of the message receiver, or an empty string for broadcast messages.
            msg: The message content.
        """
        logger.debug(f"Appending message to history: {sender} -> {receiver}: {msg}")
        key = ("", "") if receiver == "" else self.get_chat_identifier(sender, receiver)

        with self.lock:
            if key not in self.history:
                self.history[key] = []

            self.history[key].append(
                (sender, time.strftime("%m/%d %H:%M", time.localtime()), msg)
            )

        self.save_history()
        logger.debug(f"Successfully appended message to history and released lock.")

    def get_history(self, sender: str, receiver: str) -> list[tuple[str, str, str]]:
        """
        Get chat history for a conversation.

        Args:
            sender: The username of the sender.
            receiver: The username of the receiver, or an empty string for broadcast messages.

        Returns:
            A list of tuples containing chat history entries, each containing a sender, a
            timestamp, and a message.
        """
        with self.lock:
            key = (
                ("", "")
                if receiver == ""
                else self.get_chat_identifier(sender, receiver)
            )
            return self.history.get(key, [])

    def save_history(self) -> None:
        """
        Save chat history to a file.
        """
        with self.lock:
            # Join the storage directory with the filename using Path
            with open(self.history_filepath, "wb") as f:
                pickle.dump(self.history, f)

    # TODO: Abstract away the load-from-file logic that's repeated in UserManager and ChatHistory
    def load_history(self) -> dict[tuple[str, str], list[tuple[str, str, str]]]:
        """
        Load chat history from a file.

        Returns:
            A dictionary containing chat history, or an empty dictionary if the file doesn't exist.
        """
        try:
            with open(self.history_filepath, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError):
            logger.warning(
                f"Failed to load {self.history_filepath.name}; file will be created"
            )
            return {}
