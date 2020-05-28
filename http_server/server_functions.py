import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


html_files_path = os.path.join(os.getcwd(), "http_server", "html_files")


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        '': 'application/octet-stream',
        '.manifest': 'text/cache-manifest',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.svg': 'image/svg+xml',
        '.css': 'text/css',
        '.js': 'application/x-javascript',
        '.wasm': 'application/wasm',
        '.json': 'application/json',
        '.xml': 'application/xml',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=html_files_path, **kwargs)


def open_local_http_server():
    server_address = ('', 8000)

    with ThreadingHTTPServer(server_address, Handler) as httpd:
        print("Server started at http://localhost:8000")
        httpd.serve_forever()
