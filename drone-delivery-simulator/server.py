"""
SkyRoute - Autonomous Drone Delivery Simulator
Local Web Server Launcher
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    port = PORT
    # Try finding an open port starting from PORT
    while port < PORT + 20:
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                url = f"http://localhost:{port}/index.html"
                print(f"=" * 60)
                print(f"  SkyRoute 3D Drone Delivery Simulator is running!")
                print(f"  URL: {url}")
                print(f"  Directory: {DIRECTORY}")
                print(f"=" * 60)
                print("Press Ctrl+C to stop the server.")
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                httpd.serve_forever()
        except OSError:
            port += 1
            continue

if __name__ == "__main__":
    run_server()

