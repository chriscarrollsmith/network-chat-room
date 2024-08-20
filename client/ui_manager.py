import time
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from client.network_manager import NetworkManager
from client.file_manager import FileManager


class UIManager:
    def __init__(self) -> None:
        self.login_window: Optional[LoginWindow] = None
        self.main_window: Optional[MainWindow] = None


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


class MainWindow:
    def __init__(
        self,
        network_manager: NetworkManager,
        file_manager: FileManager,
    ) -> None:
        try:
            self.network_manager: NetworkManager = network_manager
            self.file_manager: FileManager = file_manager

            self.current_session: str = ""

            self.window: tk.Tk = tk.Tk()
            self.window.title("Chat Room")
            self.window.minsize(480, 320)

            self.msg: tk.StringVar = tk.StringVar()
            self.name: tk.StringVar = tk.StringVar()
            self.current_chat: tk.StringVar = tk.StringVar(value="Global Chat Room")

            # Main frame
            main_frame = tk.Frame(self.window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Top frame for user welcome message
            top_frame = tk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 10))
            self.label2: tk.Label = tk.Label(top_frame, textvariable=self.name)
            self.label2.pack()

            # Middle frame for chat and user list
            middle_frame = tk.Frame(main_frame)
            middle_frame.pack(fill=tk.BOTH, expand=True)

            # Chat frame (left side of middle frame)
            chat_frame = tk.Frame(middle_frame)
            chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

            self.label_current_chat: tk.Label = tk.Label(
                chat_frame, textvariable=self.current_chat
            )
            self.label_current_chat.pack(anchor=tk.W, pady=(0, 5))

            self.history: tk.Text = tk.Text(chat_frame)
            self.history.pack(fill=tk.BOTH, expand=True)
            self.history.configure(state="disabled")

            # User list frame (right side of middle frame)
            user_list_frame = tk.Frame(middle_frame)
            user_list_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

            tk.Label(user_list_frame, text="Online Users").pack(
                anchor=tk.W, pady=(0, 5)
            )

            self.user_list: tk.Listbox = tk.Listbox(user_list_frame)
            self.user_list.pack(fill=tk.BOTH, expand=True)
            self.user_list.bind("<<ListboxSelect>>", self.on_user_select)

            # Bottom frame for message input and buttons
            bottom_frame = tk.Frame(main_frame)
            bottom_frame.pack(fill=tk.X, pady=(10, 0))

            self.entry_msg: tk.Entry = tk.Entry(bottom_frame, textvariable=self.msg)
            self.entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            self.btn_send: tk.Button = tk.Button(
                bottom_frame, text="Send", command=self.send_message
            )
            self.btn_send.pack(side=tk.LEFT, padx=(0, 5))

            self.btn_file: tk.Button = tk.Button(
                bottom_frame, text="Send File", command=self.send_file
            )
            self.btn_file.pack(side=tk.LEFT)
            self.btn_file.configure(state="disabled")

            # Set welcome message
            self.name.set(f"Welcome, {self.network_manager.username or 'User'}")

            # Register event handlers
            # TODO: Create an event handler class to enforce the event system's API?
            # TODO: Create pydantic models for event requests and responses
            # TODO: Redefine event handler API and network_manager._receive_loop to pass output from previous handler as an argument for next?
            # (Allows separation of data extraction and processing steps from UI updates)
            self.network_manager.add_event_handler(
                "message_received", self.handle_receive_message
            )
            self.network_manager.add_event_handler(
                "file_request", self.handle_file_request
            )
            self.network_manager.add_event_handler(
                "file_response", self.handle_file_response
            )
            self.network_manager.add_event_handler("peer_left", self.handle_peer_left)
            self.network_manager.add_event_handler(
                "peer_joined", self.handle_peer_joined
            )
            # TODO: Add handler for "broadcast" event type

            self.network_manager.validate_connection_state(should_be_connected=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create main window: {str(e)}")
            raise e

    # --- Window setup and teardown ---

    def show(self) -> None:
        self.window.mainloop()
        self.network_manager.close_connection()
        self.destroy()

    def destroy(self) -> None:
        try:
            self.window.destroy()
        except:
            pass

    # --- UI control ---

    def update_user_list(self, users: dict[str, bool]) -> None:
        selected = self.user_list.curselection()
        self.user_list.delete(0, tk.END)
        for user, has_unread in users.items():
            name: str = "Global Chat Room" if user == "" else user
            if has_unread:
                name += " (*)"
            self.user_list.insert(tk.END, name)
        if selected:
            self.user_list.selection_set(selected)

    def append_message(self, sender: str, time: str, msg: str) -> None:
        self.history["state"] = "normal"
        self.history.insert(tk.END, f"{sender} - {time}\n")
        self.history.insert(tk.END, f"{msg}\n\n", "text")
        self.history.see(tk.END)
        self.history["state"] = "disabled"

    def show_file_receive_dialog(self, peer: str, filename: str, size: int) -> bool:
        messagebox.showinfo(
            "File Received", f"{peer} has sent you a file: {filename} ({size} bytes)"
        )
        return messagebox.askyesno(
            "Accept File", f"Do you want to accept the file from {peer}?"
        )

    # --- Outgoing server command triggers ---

    def on_user_select(self, event: tk.Event) -> None:
        selection = self.user_list.curselection()
        if selection:
            index = selection[0]
            value = self.user_list.get(index)
            selected_user = value.split(" (")[0]
            self.current_chat.set(f"Chatting with: {selected_user}")

            # Set current session to empty string for global chat, otherwise to selected user
            self.current_session = (
                "" if selected_user == "Global Chat Room" else selected_user
            )

            # Clear unread indicator for the selected user
            self.network_manager.send({"command": "read", "peer": self.current_session})
            self.update_user_list({self.current_session: False})

    def send_message(self) -> None:
        try:
            message = self.msg.get()
            if message:
                # Ignore empty messages
                if not message.strip():
                    return

                # Generate timestamp for the message
                timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                # Send the message to the server
                self.network_manager.send(
                    {
                        "command": "chat",
                        "peer": self.current_session,
                        "message": message,
                    }
                )

                # Clear the input field after sending
                self.msg.set("")

                # Update the UI with the sent message
                self.append_message("You", timestamp, message)
        except Exception as e:
            messagebox.showerror("Error", f"Error sending message: {str(e)}")

    def send_file(self) -> None:
        try:
            self.file_manager.send_file_request(self.current_chat.get())
        except Exception as e:
            messagebox.showerror("Error", f"Error sending file: {str(e)}")

    # --- Incoming event handlers ---

    def handle_receive_message(self, data: dict) -> None:
        """
        Handle incoming chat messages.

        Args:
            data (dict): A dictionary containing message data.
        """
        # Extract message details from the data
        sender: str = data.get("peer", "Unknown")
        message: str = data.get("message", "")
        timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # Display the received message in the UI
        self.append_message(sender, timestamp, message)

        # Handle the case where message is not from the current session
        if sender != self.current_session:
            self.update_user_list({sender: True})

    def handle_file_request(self, data: dict) -> None:
        if self.show_file_receive_dialog(data["peer"], data["filename"], data["size"]):
            self.network_manager.send(
                {"command": "file_response", "peer": data["peer"], "response": "accept"}
            )
            try:
                total_bytes, transfer_time = self.file_manager.receive_file_data(
                    data["filename"]
                )
                messagebox.showinfo(
                    "Info",
                    f"File received: {total_bytes} bytes from {data['peer']} in {transfer_time:.2f} seconds",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error receiving file: {str(e)}")
        else:
            self.network_manager.send(
                {"command": "file_response", "peer": data["peer"], "response": "deny"}
            )

    def handle_file_response(self, data: dict) -> None:
        if data["response"] == "accept":
            try:
                bytes_sent, transfer_time = self.file_manager.send_file_data(data)
                messagebox.showinfo(
                    "Info",
                    f"File sent: {bytes_sent} bytes to {data['peer']} in {transfer_time:.2f} seconds",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error sending file: {str(e)}")
        else:
            messagebox.showinfo("Info", "File transfer denied by recipient")
            self.file_manager._reset_file_state()

    def handle_peer_joined(self, data: dict) -> None:
        """
        Handle the event when a new peer joins the chat.

        Args:
            data (dict): A dictionary containing the peer information.
        """
        peer = data.get("peer")
        if peer:
            # Add the new peer to the user list
            self.update_user_list({peer: False})
            # Append a system message to the chat history
            self.append_message(
                "System",
                time.strftime("%Y-%m-%d %H:%M:%S"),
                f"{peer} has joined the chat.",
            )

    def handle_peer_left(self, data: dict) -> None:
        """
        Handle the event when a peer leaves the chat.

        Args:
            data (dict): A dictionary containing the peer information.
        """
        peer = data.get("peer")
        if peer:
            # Remove the peer from the user list
            current_users = {
                item.split(" (")[0]: False
                for item in self.user_list.get(0, tk.END)
                if item != "Global Chat Room"
            }
            if peer in current_users:
                del current_users[peer]
            self.update_user_list(current_users)
            # Append a system message to the chat history
            self.append_message(
                "System",
                time.strftime("%Y-%m-%d %H:%M:%S"),
                f"{peer} has left the chat.",
            )

            # If the current chat was with the peer who left, switch to global chat
            if self.current_session == peer:
                self.current_session = ""
                self.current_chat.set("Global Chat Room")
