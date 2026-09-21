"""Desktop entry point: run PDF Bench as a native desktop application.

Starts the local FastAPI server on a background thread, then shows the app's
UI in a native OS window (Windows Edge WebView2) instead of a web browser.
Closing the window quits everything. No browser, no console window.

Used both for `python desktop.py` and as the PyInstaller build target that
produces the standalone windowed PDFBench.exe.
"""
from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from server.main import app

HOST = "127.0.0.1"
PREFERRED_PORT = 8765
WINDOW_TITLE = "PDF Bench"


def pick_port() -> int:
    """Use 8765 if free, otherwise the next open port."""
    for port in range(PREFERRED_PORT, PREFERRED_PORT + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) != 0:  # nothing listening -> free
                return port
    return PREFERRED_PORT


def wait_until_ready(port: int, timeout: float = 30.0) -> bool:
    """Block until the server accepts connections (or time out)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) == 0:
                return True
        time.sleep(0.15)
    return False


def main():
    port = pick_port()
    url = f"http://{HOST}:{port}"

    # Run the API server on a daemon thread so it dies when the window closes.
    server = uvicorn.Server(
        uvicorn.Config(app, host=HOST, port=port, log_level="warning")
    )
    threading.Thread(target=server.run, daemon=True).start()

    wait_until_ready(port)

    # WebView2 blocks downloads unless explicitly allowed; the app's Download
    # buttons stream the finished PDF to the browser, so this must be on.
    webview.settings["ALLOW_DOWNLOADS"] = True

    # Native application window (Edge WebView2 on Windows). Blocks here until
    # the user closes the window, then the process exits and the daemon
    # server thread is torn down with it.
    webview.create_window(WINDOW_TITLE, url, width=1180, height=820, min_size=(900, 640))
    webview.start()

    server.should_exit = True


if __name__ == "__main__":
    main()
