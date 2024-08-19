import os
import time
import socket
import hashlib
import tkinter.filedialog
import tkinter.messagebox
from client.network_manager import NetworkManager


def get_file_md5(self, filepath: str) -> str:
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest().upper()


def format_file_size(size: int, suffix: str = "B") -> str:
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}{suffix}"
        size /= 1024.0
    return f"{size:.1f}Yi{suffix}"


class FileManager:
    def __init__(self, network_manager: NetworkManager):
        self.network_manager: NetworkManager = network_manager
        self._filename: str = ""
        self._filename_short: str = ""
        self._file_transfer_pending: bool = False

    def send_file_request(self, current_session: str) -> None:
        filename: str = tkinter.filedialog.askopenfilename()
        if filename == "":
            return

        self._filename = filename
        self._filename_short = os.path.basename(filename)
        size: int = os.path.getsize(filename)
        size_str: str = format_file_size(size)
        md5_checksum: str = get_file_md5(filename)

        self.network_manager.send(
            {
                "cmd": "file_request",
                "peer": current_session,
                "filename": self._filename_short,
                "size": size_str,
                "md5": md5_checksum,
            }
        )

        self._file_transfer_pending = True

    def send_file_data(self, data: dict) -> tuple[int, float]:
        try:
            total_bytes: int = 0
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((data["ip"], 1031))
                start_time: float = time.time()

                with open(self._filename, "rb") as f:
                    while True:
                        file_data = f.read(1024)
                        if not file_data:
                            break
                        total_bytes += len(file_data)
                        client.send(file_data)

            end_time: float = time.time()
            transfer_time: float = end_time - start_time
            return total_bytes, transfer_time
        finally:
            self._reset_file_state()

    def receive_file_data(self, filename: str) -> tuple[int, float]:
        total_bytes: int = 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("0.0.0.0", 1031))
            server.listen(1)
            client_socket, _ = server.accept()
            start_time: float = time.time()

            with open(filename, "wb") as f:
                while True:
                    file_data = client_socket.recv(1024)
                    if not file_data:
                        break
                    total_bytes += len(file_data)
                    f.write(file_data)

        end_time: float = time.time()
        transfer_time: float = end_time - start_time
        return total_bytes, transfer_time

    def _reset_file_state(self) -> None:
        self._filename = ""
        self._filename_short = ""
        self._file_transfer_pending = False
