import pickle
import time
from threading import Lock


class ChatHistory:
    def __init__(self) -> None:
        self.history: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
        self.lock = Lock()
        self.load_history()

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
        with self.lock:
            key = (
                ("", "")
                if receiver == ""
                else self.get_chat_identifier(sender, receiver)
            )

            if key not in self.history:
                self.history[key] = []

            self.history[key].append(
                (sender, time.strftime("%m/%d %H:%M", time.localtime()), msg)
            )

            self.save_history()

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
            with open("history.dat", "wb") as f:
                pickle.dump(self.history, f)

    def load_history(self) -> dict[tuple[str, str], list[tuple[str, str, str]]]:
        """
        Load chat history from a file.

        Returns:
            A dictionary containing chat history, or an empty dictionary if the file doesn't exist.
        """
        with self.lock:
            try:
                with open("history.dat", "rb") as f:
                    return pickle.load(f)
            except (FileNotFoundError, pickle.UnpicklingError):
                return {}
