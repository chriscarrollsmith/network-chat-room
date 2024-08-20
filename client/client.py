import logging
from tkinter import messagebox
from client.network_manager import NetworkManager
from client.ui_manager import UIManager, LoginWindow, MainWindow
from client.file_manager import FileManager
from utils.logger import configure_logger

# Configure the logger
configure_logger()

# Get a logger for this module
logger = logging.getLogger(__name__)


# TODO: Create corresponding Server class?
class Client:
    def __init__(self, server_ip: str, server_port: int):
        self.ui_manager = UIManager()
        self.network_manager = NetworkManager(server_ip, server_port)
        self.file_manager = FileManager(self.network_manager)

    def run(self) -> None:
        try:
            self.network_manager.connect()
        except Exception:
            messagebox.showerror(
                "Error",
                "Failed to connect to the server. Please check your network connection and try again.",
            )
            return

        # Initialize login window
        self.ui_manager.login_window = LoginWindow(self.network_manager)

        # Show login window and wait for user to authenticate
        auth_success = self.ui_manager.login_window.show()

        if not auth_success:
            return

        # Initialize main window
        self.ui_manager.main_window = MainWindow(
            self.network_manager, self.file_manager
        )

        # Show main window
        self.ui_manager.main_window.show()


if __name__ == "__main__":
    server_ip = "127.0.0.1"
    server_port = 8888

    app = Client(server_ip, server_port)
    app.run()
