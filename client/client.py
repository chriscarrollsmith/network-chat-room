from tkinter import messagebox
from client.network_manager import NetworkManager
from client.ui_manager import UIManager, LoginWindow, MainWindow
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

        # Initialize login window
        self.ui_manager.login_window = LoginWindow(self.network_manager)

        # Register event handlers
        self.network_manager.add_event_handler("login_result", self.handle_login_result)
        self.network_manager.add_event_handler(
            "register_result", self.handle_register_result
        )

        # Start receive loop
        self.network_manager.start_receive_loop()

        # Show login window
        auth_success = self.ui_manager.login_window.show()
        if not auth_success:
            return

        # Initialize main window
        self.ui_manager.main_window = MainWindow(
            self.network_manager, self.chat_manager, self.file_manager
        )

        # Register event handlers
        # TODO: Make this a method or create an EventManager class
        # TODO: Create an event handler class to enforce the event system's API?
        # TODO: Redefine event handler API and network_manager._receive_loop to pass output from previous handler as an argument for next?
        # (Allows separation of data extraction and processing steps from UI updates)
        self.network_manager.add_event_handler(
            "message_received", self.ui_manager.main_window.receive_message
        )
        self.network_manager.add_event_handler(
            "file_request", self.ui_manager.main_window.handle_file_request
        )
        self.network_manager.add_event_handler(
            "file_accept", self.ui_manager.main_window.handle_file_accept
        )
        self.network_manager.add_event_handler(
            "file_deny", self.ui_manager.main_window.handle_file_deny
        )
        self.network_manager.add_event_handler(
            "peer_left", self.ui_manager.main_window.handle_peer_left
        )
        self.network_manager.add_event_handler(
            "peer_joined", self.ui_manager.main_window.handle_peer_joined
        )
        # TODO: Add handler for "broadcast" event type

        self.network_manager.start_receive_loop()

        self.ui_manager.main_window.show()

    # TODO: Move these to LoginWindow class, maybe move initialization steps to init methods, and do receive_thread cleanup in `show`?
    def handle_register_result(self, data: dict) -> None:
        if self.ui_manager.login_window:
            try:
                if data.get("response") == "ok":
                    messagebox.showinfo(
                        "Success", "Registration successful. You can now log in."
                    )
                elif data.get("response") == "failed":
                    messagebox.showerror(
                        "Error", f"Registration failed: {data.get('reason')}"
                    )
                else:
                    raise Exception("Invalid response from server.")
            except Exception as e:
                messagebox.showerror("Error", f"Registration failed: {str(e)}")

    def handle_login_result(self, data: dict) -> None:
        if self.ui_manager.login_window:
            try:
                if data.get("response") == "ok":
                    self.ui_manager.login_window.authed = True
                    self.network_manager.username = data.get("username")
                    # receive_thread must be closed (rejoined) from same thread that created it or it will hang
                    self.network_manager.close_receive_thread()
                    self.ui_manager.login_window.window.quit()
                elif data.get("response") == "failed":
                    messagebox.showerror("Error", f"Login failed: {data.get('reason')}")
                else:
                    raise Exception("Invalid response from server.")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {str(e)}")


if __name__ == "__main__":
    server_ip = "127.0.0.1"
    server_port = 8888

    app = Client(server_ip, server_port)
    app.run()
