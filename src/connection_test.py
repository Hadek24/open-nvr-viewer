import platform
import subprocess
import socket
from PyQt6.QtCore import QThread, pyqtSignal

def test_ping(nvr_ip):
    """
    Comprueba si el NVR responde a un ping.

    Devuelve:
        (True, mensaje) si responde.
        (False, mensaje) si no responde.
    """
    if not nvr_ip:
        return False, "No IP address configured."

    if platform.system() == "Windows":
        command = ["ping", "-n", "1", "-w", "1000", nvr_ip]
    else:
        command = ["ping", "-c", "1", "-W", "1", nvr_ip]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )

        if result.returncode == 0:
            return True, f"Host {nvr_ip} responds to ping."

        return False, f"Host {nvr_ip} did not respond to ping."

    except subprocess.TimeoutExpired:
        return False, f"Ping to {nvr_ip} timed out."

    except OSError as error:
        return False, f"Could not execute ping: {error}"

def test_tcp_port(nvr_ip, nvr_port):
    """
    Comprueba si se puede establecer una conexión TCP
    con el puerto configurado del NVR.
    """
    try:
        with socket.create_connection(
            (nvr_ip, int(nvr_port)),
            timeout=3
        ):
            return True, f"TCP port {nvr_port} is reachable."

    except (OSError, ValueError) as error:
        return False, f"TCP port {nvr_port} failed: {error}"


class ConnectionTestThread(QThread):
    result_ready = pyqtSignal(str, bool, str)

    def __init__(self, nvr_ip, nvr_port):
        super().__init__()
        self.nvr_ip = nvr_ip
        self.nvr_port = nvr_port

    def run(self):
        ping_ok, ping_message = test_ping(self.nvr_ip)
        self.result_ready.emit("Ping", ping_ok, ping_message)

        port_ok, port_message = test_tcp_port(
            self.nvr_ip,
            self.nvr_port
        )
        self.result_ready.emit("Puerto TCP", port_ok, port_message)
