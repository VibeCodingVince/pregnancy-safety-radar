import http.server, ssl, sys

handler = http.server.SimpleHTTPRequestHandler
server = http.server.HTTPServer(("0.0.0.0", 8443), handler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain("cert.pem", "key.pem")
server.socket = ctx.wrap_socket(server.socket, server_side=True)
print(f"Serving on https://0.0.0.0:8443")
server.serve_forever()
