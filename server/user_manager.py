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

    def register(self, usr: str, pwd: str) -> bool:
        """
        Register a new user.

        Args:
            usr: The username to register.
            pwd: The password for the new user.

        Returns:
            True if registration is successful, False if the username already exists.
        """
        with self.lock:
            if usr not in self.users:
                self.users[usr] = pwd
                self.save_users()
                return True
            return False

    def validate(self, usr: str, pwd: str) -> bool:
        """
        Validate user credentials.

        Args:
            usr: The username to validate.
            pwd: The password to validate.

        Returns:
            True if credentials are valid, False otherwise.
        """
        with self.lock:
            return usr in self.users and self.users[usr] == pwd

    def save_users(self) -> None:
        """
        Save user data to a file.
        """
        with self.lock:
            with open("users.dat", "wb") as f:
                pickle.dump(self.users, f)
