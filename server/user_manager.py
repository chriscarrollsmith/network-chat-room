import pickle
import threading


class UserManager:
    def __init__(self) -> None:
        self.users: dict[str, str] = self.load_users()
        self.lock: threading.Lock = threading.Lock()

    def load_users(self) -> dict[str, str]:
        """
        Load user data from a file.

        Returns:
            A dictionary containing user data, or an empty dictionary if the file doesn't exist.
        """
        try:
            with open("users.dat", "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError):
            return {}

    def register(self, username: str, password: str) -> bool:
        """
        Register a new user.

        Args:
            username: The username to register.
            password: The password for the new user.

        Returns:
            True if registration is successful, False if the username already exists.
        """
        with self.lock:
            if username not in self.users:
                self.users[username] = password
                self.save_users()
                return True
            return False

    def validate(self, username: str, password: str) -> bool:
        """
        Validate user credentials.

        Args:
            username: The username to validate.
            password: The password to validate.

        Returns:
            True if credentials are valid, False otherwise.
        """
        with self.lock:
            return username in self.users and self.users[username] == password

    def save_users(self) -> None:
        """
        Save user data to a file.
        """
        with self.lock:
            with open("users.dat", "wb") as f:
                pickle.dump(self.users, f)
