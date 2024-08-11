from tkinter import messagebox
from client.network_manager import NetworkManager
from client.ui_manager import UIManager
from client.chat_manager import ChatManager
from client.file_manager import FileManager


# TODO: Create corresponding Server class?
class Client:
    def __init__(self, server_ip: str, server_port: int):
        self.ui_manager = UIManager()
        self.network_manager = NetworkManager(server_ip, server_port)
        self.chat_manager = ChatManager(self.network_manager)
        self.file_manager = FileManager(self.network_manager)

    def run(self) -> None:
        if not self.network_manager.connect():
            messagebox.showerror(
                "Error",
                "Failed to connect to the server. Please check your network connection and try again.",
            )
            return

        login_successful = self.ui_manager.show_login(self.network_manager)

        if login_successful:
            self.ui_manager.show_main(
                self.network_manager, self.chat_manager, self.file_manager
            )

        # Register event handlers (TODO: Make this a method)
        # TODO: Create an event handler class and/or decorator to perform the check for the main window and enforce the API?
        # TODO: Redefine event handler API and network_manager._receive_loop to pass output from previous handler as an argument for next?
        # (Allows separation of data extraction and processing steps from UI updates)
        # TODO: Register a tuple of handler lists to handle both the operations and the failure cases?
        # (Requires adding try-except to network_manager._receive_loop and modifying signature of network_manager.add_event_handler)
        # (This is probably the wrong abstraction, because it doesn't allow sufficiently flexible error handling)
        if self.ui_manager.main_window:
            self.network_manager.add_event_handler(
                "message_received", self.ui_manager.main_window.receive_message
            )
            self.network_manager.add_event_handler(
                "file_request", self.ui_manager.main_window.handle_file_request
            )
            self.network_manager.add_event_handler(
                "update_user_list", self.ui_manager.main_window.update_user_list
            )
            self.network_manager.add_event_handler(
                "file_accept", self.ui_manager.main_window.handle_file_accept
            )
            self.network_manager.add_event_handler(
                "file_deny", self.ui_manager.main_window.handle_file_deny
            )
            # TODO: Add more handlers?


if __name__ == "__main__":
    server_ip = "127.0.0.1"
    server_port = 8888

    app = Client(server_ip, server_port)
    app.run()
