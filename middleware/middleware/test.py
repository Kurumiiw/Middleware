import socket

HOST = input("addr: ")
MIDDLEWARE_PORT = 5000


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    choice = input("Listen for connection? (y/n) ")

    if choice == "y":
        print("[Socket] Binding address", HOST, "with port",
              MIDDLEWARE_PORT, "for", s.type, "...")
        s.bind((HOST, MIDDLEWARE_PORT))
        print("[Socket] Listening")
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(f"[Socket] Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)
    else:
        print("[Socket] Sending data")
        s.connect((HOST, MIDDLEWARE_PORT))
        s.sendall(bytes(input("string: "), 'ascii'))
        data = s.recv(1024)
        print(f"Received {data!r}")

    print("Goodbye")
