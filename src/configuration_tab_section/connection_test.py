
"""
NVR connection diagnostics.

Provides basic connectivity tests for an NVR:
- ICMP echo request using the system ping command.
- TCP connection to the configured NVR port.

ConnectionTestThread executes both tests in a background thread
and emits their results through a Qt signal.
"""

import platform
import socket
import subprocess

from PyQt6.QtCore import QThread, pyqtSignal


def test_ping(nvr_ip):
    """
    Check whether the NVR responds to a ping request.

    Args:
        nvr_ip: IP address or hostname of the NVR.

    Returns:
        tuple[bool, str]:
            True and a success message if the host responds.
            False and an error message otherwise.
    """
    if not nvr_ip:
        return False, "No IP address configured."

    # Build the ping command according to the operating system.
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
    Check whether a TCP connection can be established to the NVR port.

    Args:
        nvr_ip: IP address or hostname of the NVR.
        nvr_port: TCP port to test.

    Returns:
        tuple[bool, str]:
            True and a success message if the connection succeeds.
            False and an error message if it fails.
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
    """
    Run NVR connectivity tests without blocking the application UI.

    The thread executes the ping test first, followed by the TCP port
    test. Each result is emitted through result_ready as soon as the
    corresponding test finishes.
    """

    # Signal arguments: test name, success status, result message.
    result_ready = pyqtSignal(str, bool, str)

    def __init__(self, nvr_ip, nvr_port):
        """Initialize the thread with the NVR address and TCP port."""
        super().__init__()

        self.nvr_ip = nvr_ip
        self.nvr_port = nvr_port

    def run(self):
        """Execute the connectivity tests and emit their results."""

        # Test basic IP reachability.
        ping_ok, ping_message = test_ping(self.nvr_ip)
        self.result_ready.emit("Ping", ping_ok, ping_message)

        # Test TCP connectivity to the configured port.
        port_ok, port_message = test_tcp_port(
            self.nvr_ip,
            self.nvr_port
        )
        self.result_ready.emit("Puerto TCP", port_ok, port_message)
