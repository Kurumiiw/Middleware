import socket

HOST = input("addr: ")
MIDDLEWARE_PORT = 5000


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("[Socket] Binding address", HOST, "with port",
          MIDDLEWARE_PORT, "for", s.type, "...")
    s.bind((HOST, MIDDLEWARE_PORT))

    print("[Socket] Listening")
    s.listen()
