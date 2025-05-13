import socket
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading

def run_udp_server(host='127.0.0.1', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"UDP server is running on {host}:{port}")

    os.makedirs("storage", exist_ok=True)
    json_path = os.path.join("storage", "data.json")

    while True:
        data, _ = sock.recvfrom(1024)
        decoded = data.decode()

        parsed = dict([item.split("=") for item in decoded.split("&")])
        timestamp = str(datetime.now())

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            content = {}
        content[timestamp] = parsed

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/':
            self.send_html("templates/index.html")
        elif path == '/message':
            self.send_html("templates/message.html")
        elif path.startswith('/static/'):
            self.send_static(path[1:])
        else:
            self.send_html("templates/error.html", status=404)

    def do_POST(self):
        if self.path == '/message':
            length = int(self.headers.get('Content-Length', 0))
            data = self.rfile.read(length).decode()

            self.send_to_socket(data)
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()

    def send_html(self, filename, status=200):
        try:
            with open(filename, 'rb') as f:
                self.send_response(status)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            if filename != 'templates/error.html':
                self.send_html("templates/error.html", 404)

    def send_static(self, filepath):
        try:
            with open(filepath, "rb") as f:
                if filepath.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif filepath.endswith(".png"):
                    self.send_header("Content-type", "image/png")
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_html("templates/error.html", 404)

    def send_to_socket(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data.encode(), ("127.0.0.1", 5000))


def run_http_server():
    httpd = HTTPServer(("0.0.0.0", 3000), WebHandler)
    print("HTTP server running on port 3000")
    httpd.serve_forever()


if __name__ == '__main__':
    t1 = threading.Thread(target=run_http_server)
    t2 = threading.Thread(target= run_udp_server)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
