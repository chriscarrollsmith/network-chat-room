import os
import traceback
import pickle
import threading
import logging

logger = logging.getLogger(__name__)


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
                users = pickle.load(f)
            return users
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            logger.warning(f"Failed to load users: {str(e)}")
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
        logger.debug(f"Attempting to register user: {username}")
        try:
            if not self.lock.acquire(timeout=5):
                return False
            try:
                if username not in self.users:
                    self.users[username] = password
                    self.save_users()
                    logger.info(f"User {username} registered successfully")
                    return True
                logger.warning(
                    f"Registration failed: Username {username} already exists"
                )
                return False
            finally:
                self.lock.release()
                logger.debug("Lock released")
        except Exception as e:
            logger.error(f"Unexpected error in register method: {str(e)}")
            logger.error(traceback.format_exc())
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
            logger.debug(
                f"Validating user {username}: {'Success' if is_valid else 'Failed'}"
            )
            return is_valid

    def save_users(self) -> None:
        logger.debug("Saving users to file")
        try:
            file_path = "users.dat"
            with open(file_path, "wb") as f:
                pickle.dump(self.users, f)
        except Exception as e:
            logger.error(f"Failed to save users: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(traceback.format_exc())
