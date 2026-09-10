"""Desktop entry point: start the local server and open the browser.

Used both for `python desktop.py` and as the PyInstaller build target that
produces the standalone DeskewPDF.exe.
"""
from __future__ import annotations

import socket
import threading
import time
import webbrowser

import uvicorn

from server.main import app

HOST = "127.0.0.1"
PREFERRED_PORT = 8765


def pick_port() -> int:
    """Use 8765 if free, otherwise the next open port."""
    for port in range(PREFERRED_PORT, PREFERRED_PORT + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) != 0:  # nothing listening -> free
                return port
    return PREFERRED_PORT


def open_when_ready(port: int):
    url = f"http://{HOST}:{port}"
    # wait until the server accepts connections, then open the browser
    for _ in range(100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) == 0:
                break
        time.sleep(0.2)
    webbrowser.open(url)


def main():
    port = pick_port()
    print("=" * 56)
    print(f"  DeskewPDF is running at  http://{HOST}:{port}")
    print("  Your browser will open automatically.")
    print("  Keep this window open while you use the app.")
    print("  Close this window to quit.")
    print("=" * 56)
    threading.Thread(target=open_when_ready, args=(port,), daemon=True).start()
    uvicorn.run(app, host=HOST, port=port, log_level="info")


if __name__ == "__main__":
    main()
