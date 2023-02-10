import socket
import threading

HOST = input("addr: ")
MIDDLEWARE_PORT = 5000

def receive(sock):
    try:
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    print("Received:",data.decode('utf-8'))
            except:
                print("Error receiving data")
                break
    except KeyboardInterrupt:
        return

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    choice = input("Listen for connection? (y/n) ")

    if choice == "y":
        while True:
            print("[Socket] Binding address", HOST, "with port",
                MIDDLEWARE_PORT, "for", s.type, "...")
            s.bind((HOST, MIDDLEWARE_PORT))
            print("[Socket] Listening")
            s.listen()
            conn, addr = s.accept()
            print("[Socket] Connected to", addr)
            receiveThread = threading.Thread(target=receive, args=(conn,))
            receiveThread.daemon = True
            receiveThread.start()
            try:
                while True:
                    try:
                        data = input()
                        if data:
                            conn.sendall(bytes(data, 'utf-8'))
                    except:
                        print("Error sending data")
                        receiveThread.join()
                        break
            except KeyboardInterrupt:
                exit()
    else:
        print("[Socket] Sending data")
        s.connect((HOST, MIDDLEWARE_PORT))
        receiveThread = threading.Thread(target=receive, args=(s,))
        receiveThread.daemon = True
        receiveThread.start()
        try:
            while True:
                try:
                    data = input("string: ")
                    if data:
                        s.sendall(bytes(data, 'utf-8'))
                except:
                    print("Error sending data")
                    receiveThread.join()
                    break
        except KeyboardInterrupt:
            exit()

    print("Goodbye")
