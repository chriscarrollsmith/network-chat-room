import tkinter as tk
from tkinter import messagebox
from client.network_manager import NetworkManager


class LoginWindow:
    def __init__(self, network_manager: NetworkManager) -> None:
        try:
            self.network_manager: NetworkManager = network_manager

            self.authed: bool = False

            self.window: tk.Tk = tk.Tk()
            self.username: tk.StringVar = tk.StringVar()
            self.password: tk.StringVar = tk.StringVar()

            self.window.title("Login")

            # Set minimum size instead of fixed size
            self.window.minsize(300, 180)

            # Allow window to be resized
            self.window.resizable(True, True)

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

    def show(self):
        self.window.mainloop()
        try:
            self.network_manager.clear_event_handlers()
            if not self.authed:
                self.network_manager.close_connection()
            self.destroy()
            return self.authed
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close login window: {str(e)}")

    def destroy(self):
        try:
            self.window.destroy()
        except:
            pass

    # --- Outgoing server command triggers ---

    def login(self) -> None:
        # To get value of tk.StringVar, use .get()
        username: str = self.username.get()
        password: str = self.password.get()
        try:
            self.network_manager.send(
                {"command": "login", "username": username, "password": password}
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send login request: {str(e)}")

    def register(self) -> None:
        # To get value of tk.StringVar, use .get()
        username: str = self.username.get()
        password: str = self.password.get()
        self.network_manager.send(
            {"command": "register", "username": username, "password": password}
        )

    # --- Incoming event handlers ---

    def handle_register_result(self, data: dict) -> None:
        try:
            if data.get("response") == "ok":
                messagebox.showinfo(
                    "Success", "Registration successful. You can now log in."
                )
            elif data.get("response") == "fail":
                messagebox.showerror(
                    "Error", f"Registration failed: {data.get('reason')}"
                )
            else:
                raise Exception("Invalid response from server.")
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")

    def handle_login_result(self, data: dict) -> None:
        try:
            if data.get("response") == "ok":
                self.authed = True
                self.network_manager.username = str(data.get("username"))
                self.window.quit()
            elif data.get("response") == "fail":
                messagebox.showerror("Error", f"Login failed: {data.get('reason')}")
            else:
                raise Exception("Invalid response from server.")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
