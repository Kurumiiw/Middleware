from middleware.middlewareAPI import *


class ChatService:
    def __init__(self, name: str, address: tuple[str, int]):
        self.hostConnections: list[MiddlewareReliable] = []
        self.address = address
        self.name = name
        self.mw = MiddlewareAPI.reliable(address[0], address[1], timeout=None)
        self.mw.bind(self.address)
        self.active = True

    def hostChat(self) -> None:
        """
        Hosts a chat, listens for an inital connection, then starts a thread to listen for more connections
        """

        self.mw.listen()
        print(f"\nWaiting for connections on {self.address}...\n")
        conn, addr = self.mw.accept()
        self.hostConnections.append(conn)
        threading.Thread(target=self.listenForConnections, daemon=True).start()
        threading.Thread(
            target=self.handleConnection, args=(conn, addr), daemon=True
        ).start()
        self.hostSendData()

    def listenForConnections(self) -> None:
        """
        Listens for connections, adds them to the list of connections, and starts a thread to handle them
        """
        while True:
            self.mw.listen()
            conn, addr = self.mw.accept()
            self.hostConnections.append(conn)
            threading.Thread(
                target=self.handleConnection, args=(conn, addr), daemon=True
            ).start()

    def handleConnection(self, conn: MiddlewareReliable, addr: tuple[str, int]) -> None:
        """
        Handles a connection, listens for data and sends them to the other connections.
        Prints the received data to the console.
        """
        self.distributeData(
            conn,
            ("\n" + addr[0] + ":" + str(addr[1]) + " joined the chat").encode("utf-8"),
        )
        print(f"\n{addr[0]}:{addr[1]} joined the chat\n")
        while True:
            try:
                data = conn.receive().decode("utf-8")
            except ConnectionResetError:
                self.hostConnections.remove(conn)
                self.distributeData(
                    conn,
                    ("\n" + addr[0] + ":" + str(addr[1]) + " left the chat").encode(
                        "utf-8"
                    ),
                )
                conn.close()
                break
            if data != "":
                print(data)
                self.distributeData(conn, data.encode("utf-8"))
            else:
                self.hostConnections.remove(conn)
                self.distributeData(
                    conn,
                    ("\n" + addr[0] + ":" + str(addr[1]) + " left the chat").encode(
                        "utf-8"
                    ),
                )
                conn.close()
                break

    def hostSendData(self) -> None:
        """
        Sends data from the host to the other connections, and prints the data to the console.
        """
        while True:
            message = input()
            if not self.active:
                print("Chat ended")
                exit()
            try:
                if message == "exit":
                    self.active = False
                    for conn in self.hostConnections:
                        conn.send("Chat ended".encode("utf-8"))
                        conn.close()
                    self.mw.close()
                    exit()
                else:
                    print("\n" + self.name + ": " + message)
                    for conn in self.hostConnections:
                        conn.send(
                            ("\n" + self.name + "(you): " + message).encode("utf-8")
                        )
            except Exception as e:
                print(e)
                break

    def distributeData(self, senderConn: MiddlewareReliable, data: bytes) -> None:
        """
        Sends data to all connections except the sender (senderConn)
        """

        for conn in self.hostConnections:
            if conn != senderConn:
                conn.send(data)

    def connectToChat(self, address: tuple[str, int]) -> None:
        """
        Connects to a hosted chat and starts a thread to listen for data.
        """
        self.mw.connect(address)
        threading.Thread(target=self.receiveData, args=(), daemon=True).start()
        print(f"\nConnected to chat on {address}\n")
        self.sendData()

    def sendData(self) -> None:
        """
        Sends text input in the form of bytes to the host
        """
        while True:
            message = input()
            if not self.active:
                print("Chat ended")
                exit()
            try:
                if message == "exit":
                    self.active = False
                    self.mw.send(f"{self.address} left the chat".encode("utf-8"))
                    print("Chat ended")
                    self.mw.close()
                    exit()
                else:
                    print("\n" + self.name + ": " + message)
                    self.mw.send(("\n" + self.name + ": " + message).encode("utf-8"))
            except Exception as e:
                print(e)
                break

    def receiveData(self) -> bytes:
        """
        Receives data from the host
        """
        try:
            data = self.mw.receive()
            return data
        except ConnectionResetError:
            self.close()

    def printMessage(self, message: str) -> None:
        """
        Prints a message
        """
        print(message)

    def receive_and_print_messages(self) -> None:
        """
        Receives data, decodes the data into str, and prints the message.
        """
        while self.active:
            data = self.receiveData()
            message = data.decode("utf-8")
            if message != "":
                self.printMessage(message)
            elif data == "\nChat ended\n":
                self.close()
                self.active = False
                break

    def close(self) -> None:
        """
        Closes the connection
        """
        self.mw.close()


if __name__ == "__main__":
    name = input("Choose username: ")
    i = input("Host (h) or connect (c)? ")
    if i == "h" or i == "H":
        port = int(input("What port do you want to host on?"))
        while port < 0 or port > 65535:
            print("Invalid port")
            port = int(input("What port do you want to host on?"))
        service = ChatService(name, ("", port))
        service.hostChat()
    elif i == "c" or i == "C":
        port = int(input("What port do you want to use?"))
        while port < 0 or port > 65535:
            print("Invalid port")
            port = int(input("What port do you want to host on?"))
        service = ChatService(name, ("", port))
        hostIP = input("Host IP? ")
        hostPort = int(input("Host Port? "))
        while hostPort < 0 or port > 65535:
            print("Invalid port")
            hostPort = int(input("What port do you want to host on?"))
        if hostIP == "":
            hostIP = "localhost"
        service.connectToChat((hostIP, hostPort))
