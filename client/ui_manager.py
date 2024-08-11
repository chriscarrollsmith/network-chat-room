import time
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from client.network_manager import NetworkManager
from client.chat_manager import ChatManager
from client.file_manager import FileManager


class UIManager:
    def __init__(self) -> None:
        self.login_window: Optional[LoginWindow] = None
        self.main_window: Optional[MainWindow] = None

    def show_login(self, network_manager: NetworkManager) -> bool:
        self.login_window = LoginWindow(network_manager)
        return self.login_window.run_login_loop()

    def show_main(
        self,
        network_manager: NetworkManager,
        chat_manager: ChatManager,
        file_manager: FileManager,
    ) -> None:
        self.main_window = MainWindow(network_manager, chat_manager, file_manager)
        self.main_window.show()


class LoginWindow:
    # TODO: Add a cancel or "x" button to exit program
    def __init__(self, network_manager: NetworkManager) -> None:
        self.network_manager: NetworkManager = network_manager

        self.window: tk.Tk = tk.Tk()
        self.username: tk.StringVar = tk.StringVar()
        self.password: tk.StringVar = tk.StringVar()
        self.login_successful = False

        self.window.geometry("320x240")
        self.window.title("Login")
        self.window.resizable(width=False, height=False)

        self.username_label: tk.Label = tk.Label(self.window, text="Username")
        self.username_label.place(relx=0.055, rely=0.1, height=31, width=89)

        self.username_field: tk.Entry = tk.Entry(
            self.window, textvariable=self.username
        )
        self.username_field.place(relx=0.28, rely=0.11, height=26, relwidth=0.554)

        self.password_label: tk.Label = tk.Label(self.win, text="Password")
        self.password_label.place(relx=0.055, rely=0.27, height=31, width=89)

        self.password_field: tk.Entry = tk.Entry(
            self.window, show="*", textvariable=self.password
        )
        self.password_field.place(relx=0.28, rely=0.28, height=26, relwidth=0.554)

        self.login_button: tk.Button = tk.Button(
            self.window, text="Login", command=self.handle_login
        )
        self.login_button.place(relx=0.13, rely=0.6, height=32, width=88)

        self.register_button: tk.Button = tk.Button(
            self.window, text="Register", command=self.handle_register
        )
        self.register_button.place(relx=0.6, rely=0.6, height=32, width=88)

    # TODO: Handle login and registration responses with an event loop? This would allow login events not directly triggered by the UI, e.g. magic link login
    def handle_login(self) -> None:
        username: str = self.username.get()
        password: str = self.password.get()
        response: Optional[dict[str, str]] = self.network_manager.login(
            username, password
        )
        if response and response["response"] == "ok":
            self.login_successful = True
            self.window.quit()
        else:
            messagebox.showerror(
                "Error", "Login failed. Please check your credentials."
            )

    def handle_register(self) -> None:
        username: str = self.username.get()
        password: str = self.password.get()
        response: bool = self.network_manager.register(username, password)
        if response:
            messagebox.showinfo(
                "Success", "Registration successful. You can now log in."
            )
        else:
            messagebox.showerror(
                "Error", "Registration failed. Please try a different username."
            )

    def run_login_loop(self) -> bool:
        self.window.mainloop()
        self.window.destroy()
        return self.login_successful


class MainWindow:
    def __init__(
        self,
        network_manager: NetworkManager,
        chat_manager: ChatManager,
        file_manager: FileManager,
    ) -> None:
        self.network_manager: NetworkManager = network_manager
        self.chat_manager: ChatManager = chat_manager
        self.file_manager: FileManager = file_manager

        self.win: tk.Tk = tk.Tk()
        self.win.geometry("480x320")
        self.win.title("Chat Room")
        self.win.resizable(width=False, height=False)

        self.msg: tk.StringVar = tk.StringVar()
        self.name: tk.StringVar = tk.StringVar()

        self.user_list: tk.Listbox = tk.Listbox(self.win)
        self.user_list.place(relx=0.75, rely=0.15, relheight=0.72, relwidth=0.23)
        self.user_list.bind("<<ListboxSelect>>", self.on_user_select)

        self.label1: tk.Label = tk.Label(self.win, text="Online Users")
        self.label1.place(relx=0.76, rely=0.075, height=21, width=101)

        self.history: tk.Text = tk.Text(self.win)
        self.history.place(relx=0.02, rely=0.24, relheight=0.63, relwidth=0.696)
        self.history.configure(state="disabled")

        self.entry_msg: tk.Entry = tk.Entry(self.win, textvariable=self.msg)
        self.entry_msg.place(relx=0.02, rely=0.9, height=24, relwidth=0.59)

        self.btn_send: tk.Button = tk.Button(self.win, text="Send")
        self.btn_send.place(relx=0.62, rely=0.89, height=28, width=45)

        self.btn_file: tk.Button = tk.Button(self.win, text="Send File")
        self.btn_file.place(relx=0.752, rely=0.89, height=28, width=108)
        self.btn_file.configure(state="disabled")

        self.label2: tk.Label = tk.Label(self.win, textvariable=self.name)
        self.label2.place(relx=0.24, rely=0.0, height=57, width=140)

        self.current_chat: tk.StringVar = tk.StringVar(value="Global Chat Room")
        self.label_current_chat: tk.Label = tk.Label(
            self.win, textvariable=self.current_chat
        )
        self.label_current_chat.place(relx=0.02, rely=0.18, height=21, width=200)

        if self.btn_send:
            self.btn_send.configure(command=lambda: self.send_message(""))

        if self.btn_file:
            self.btn_file.configure(command=lambda: self.send_file(""))

        if self.name:
            self.name.set(
                f"Welcome, {getattr(self.network_manager, 'username', 'User')}"
            )

    def show(self) -> None:
        self.win.mainloop()

    def destroy(self) -> None:
        self.win.destroy()

    def on_user_select(self, event: tk.Event) -> None:
        selection = self.user_list.curselection()
        if selection:
            index = selection[0]
            value = self.user_list.get(index)
            selected_user = value.split(" (")[0]  # Remove the (*) if present
            self.current_chat.set(f"Chatting with: {selected_user}")
            # Set current session to empty string for global chat, otherwise to selected user
            self.current_session = (
                "" if selected_user == "Global Chat Room" else selected_user
            )
            # Clear unread indicator for the selected user
            self.network_manager.send({"cmd": "read", "peer": self.current_session})
            self.update_user_list({self.current_session: False})

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

    def send_message(self, message: str) -> None:
        try:
            self.chat_manager.send_message(message, self.append_message)
        except Exception as e:
            messagebox.showerror("Error", f"Error sending message: {str(e)}")

    def receive_message(self, data: dict) -> None:
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
        if sender != self.chat_manager.current_session:
            self.update_user_list({sender: True})

    def append_message(self, sender: str, time: str, msg: str) -> None:
        self.history["state"] = "normal"
        self.history.insert(tk.END, f"{sender} - {time}\n")
        self.history.insert(tk.END, f"{msg}\n\n", "text")
        self.history.see(tk.END)
        self.history["state"] = "disabled"

    def send_file(self, filename: str) -> None:
        try:
            self.file_manager.send_file_request(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Error sending file: {str(e)}")

    def show_file_receive_dialog(self, peer: str, filename: str, size: int) -> bool:
        messagebox.showinfo(
            "File Received", f"{peer} has sent you a file: {filename} ({size} bytes)"
        )
        return messagebox.askyesno(
            "Accept File", f"Do you want to accept the file from {peer}?"
        )

    def handle_file_request(self, data: dict) -> None:
        if self.show_file_receive_dialog(data["peer"], data["filename"], data["size"]):
            self.network_manager.send({"cmd": "file_accept", "peer": data["peer"]})
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
            self.network_manager.send({"cmd": "file_deny", "peer": data["peer"]})

    def handle_file_accept(self, data: dict) -> None:
        try:
            bytes_sent, transfer_time = self.file_manager.send_file_data(data)
            messagebox.showinfo(
                "Info",
                f"File sent: {bytes_sent} bytes to {data['peer']} in {transfer_time:.2f} seconds",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error sending file: {str(e)}")

    def handle_file_deny(self) -> None:
        messagebox.showinfo("Info", "File transfer denied by recipient")
        self.file_manager._reset_file_state()
