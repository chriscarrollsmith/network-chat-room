import tkinter as tk
from tkinter import messagebox
from typing import Literal
from client.network_manager import NetworkManager


class LoginWindow:
    def __init__(self, network_manager: NetworkManager) -> None:
        try:
            self.network_manager: NetworkManager = network_manager

            # Create and set up tkinter "Login" window
            self.window: tk.Tk = tk.Tk()
            self.window.title("Login")
            self.window.minsize(300, 180)
            self.window.resizable(True, True)

            # Initialize auth state variables
            self.authed: bool = False
            self.username: tk.StringVar = tk.StringVar(self.window)
            self.password: tk.StringVar = tk.StringVar(self.window)

            # Main frame
            main_frame = tk.Frame(self.window, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Username row
            username_frame = tk.Frame(main_frame)
            username_frame.pack(fill=tk.X, pady=5)
            tk.Label(username_frame, text="Username", width=10).pack(side=tk.LEFT)
            tk.Entry(username_frame, textvariable=self.username).pack(
                side=tk.RIGHT, expand=True, fill=tk.X
            )

            # Password row
            password_frame = tk.Frame(main_frame)
            password_frame.pack(fill=tk.X, pady=5)
            tk.Label(password_frame, text="Password", width=10).pack(side=tk.LEFT)
            tk.Entry(password_frame, show="*", textvariable=self.password).pack(
                side=tk.RIGHT, expand=True, fill=tk.X
            )

            # Buttons row
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=20)
            tk.Button(button_frame, text="Login", command=self.login).pack(
                side=tk.LEFT, expand=True, padx=5
            )
            tk.Button(button_frame, text="Register", command=self.register).pack(
                side=tk.RIGHT, expand=True, padx=5
            )

            # Bind Enter key to login
            self.window.bind("<Return>", self.login)

            # Register event handlers
            self.network_manager.add_event_handler(
                "login_result", self.handle_login_result
            )
            self.network_manager.add_event_handler(
                "register_result", self.handle_register_result
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create login window: {str(e)}")
            raise e

        # --- Window setup and teardown ---

    def show(self) -> bool:
        # Start the UI loop
        self.window.mainloop()

        exceptions = []

        # Clean up the connection after window is closed if the user didn't log in
        try:
            if not self.authed:
                self.network_manager.close_connection()
        except Exception as e:
            exceptions.append(f"Failed to close connection: {str(e)}")

        # Clean up event handlers
        try:
            self.network_manager.clear_event_handlers()
        except Exception as e:
            exceptions.append(f"Failed to clear event handlers: {str(e)}")

        # Destroy the window
        try:
            self.window.destroy()
        except Exception as e:
            exceptions.append(f"Failed to destroy window: {str(e)}")

        # Display a generic error message if any exceptions occurred
        if exceptions:
            messagebox.showerror(
                "Error", "An error occurred when closing the login window."
            )
            raise Exception(" | ".join(exceptions))

        return self.authed

    # --- Outgoing server command triggers ---

    def login(self) -> None:
        self.send_authentication_request("login")

    def register(self) -> None:
        self.send_authentication_request("register")

    def send_authentication_request(self, command: str) -> None:
        # To get value of tk.StringVar, use .get()
        username: str = self.username.get()
        password: str = self.password.get()
        try:
            self.network_manager.send(
                {"command": command, "username": username, "password": password}
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send {command} request: {str(e)}")

    # --- Incoming event handlers ---

    def handle_register_result(self, data: dict) -> None:
        if data.get("response") == "ok":
            messagebox.showinfo("Success", "Registration successful!")
        else:
            self.handle_authentication_failure(data, "register")

    def handle_login_result(self, data: dict) -> None:
        if data.get("response") == "ok":
            self.authed = True
            self.network_manager.username = str(data.get("username"))
            self.window.quit()
        else:
            self.handle_authentication_failure(data, "login")

    def handle_authentication_failure(
        self, data: dict, command: Literal["login", "register"]
    ) -> dict | None:
        try:
            if data.get("response") == "fail":
                raise Exception(data.get("reason"))
            elif data.get("response") != "ok":
                raise Exception("Invalid response from server.")
            else:
                raise Exception("Unknown error occurred.")
        except Exception as e:
            messagebox.showerror("Error", f"{command.capitalize()} failed: {str(e)}")
            return None
