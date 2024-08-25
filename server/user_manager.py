import os
import traceback
import pickle
import threading
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure that the data directory exists
STORAGE_DIR: Path = Path.cwd() / os.getenv("STORAGE_DIR", ".ncr-data")
STORAGE_DIR.mkdir(exist_ok=True)


class UserManager:
    def __init__(self) -> None:
        self.users_file: Path = STORAGE_DIR / "users.dat"
        self.logger = logging.getLogger(__name__)

        # Log absolute path of users file
        self.logger.debug(f"Users file path: {self.users_file.absolute()}")

        self.users: dict[str, str] = self.load_users()
        self.lock: threading.Lock = threading.Lock()

    def load_users(self) -> dict[str, str]:
        """
        Load user data from a file.

        Returns:
            A dictionary containing user data, or an empty dictionary if the file doesn't exist.
        """
        try:
            with open(self.users_file, "rb") as f:
                users = pickle.load(f)
            return users
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            self.logger.warning(
                f"Failed to load {self.users_file.name}; file will be created"
            )
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
        self.logger.debug(f"Attempting to register user: {username}")
        try:
            if not self.lock.acquire(timeout=5):
                return False
            try:
                if username not in self.users:
                    self.users[username] = password
                    self.save_users()
                    self.logger.info(f"User {username} registered successfully")
                    return True
                self.logger.warning(
                    f"Registration failed: Username {username} already exists"
                )
                return False
            finally:
                self.lock.release()
                self.logger.debug("Lock released")
        except Exception as e:
            self.logger.error(f"Unexpected error in register method: {str(e)}")
            self.logger.error(traceback.format_exc())
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
            is_valid = username in self.users and self.users[username] == password
            self.logger.debug(
                f"Validating user {username}: {'Success' if is_valid else 'Failed'}"
            )
            return is_valid

    def save_users(self) -> None:
        self.logger.debug("Saving users to file")
        try:
            with open(self.users_file, "wb") as f:
                pickle.dump(self.users, f)
        except Exception as e:
            self.logger.error(f"Failed to save users: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(traceback.format_exc())
