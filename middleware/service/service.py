from middleware.middlewareAPI import *

class ChatService():

    def __init__(self, name: str, address: tuple[str, int]):

        self.hostConnections = []
        self.address = address
        self.name = name
        self.mw = MiddlewareAPI.reliable(address[0], address[1], timeout=None)
        self.mw.bind(self.address)
        self.active = True
    
    def hostChat(self):
        """
        Hosts a chat, listens for an initail connection, then starts a thread to listen for more connections
        """

        self.mw.listen()
        print(f"\nWaiting for connections on {self.address}...\n")
        conn, addr = self.mw.accept()
        self.hostConnections.append(conn)
        threading.Thread(target=self.listenForConnections, daemon=True).start()
        threading.Thread(target=self.handleConnection, args=(conn, addr), daemon=True).start()
        self.hostSendMessages()
        

    def listenForConnections(self):
        """
        Listens for connections and adds them to the list of connections
        """
        while True:
            self.mw.listen()
            conn, addr = self.mw.accept()
            self.hostConnections.append(conn)
            threading.Thread(target=self.handleConnection, args=(conn, addr), daemon=True).start()

    def handleConnection(self, conn, addr):
        """
        Handles a connection, listens for messages and sends them to the other connections
        """
        self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" joined the chat").encode("utf-8"))
        print(f"\n{addr[0]}:{addr[1]} joined the chat\n")
        while True:
            try:
                data = conn.receive().decode("utf-8")
            except ConnectionResetError:
                self.hostConnections.remove(conn)
                self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" left the chat").encode("utf-8"))
                conn.close()
                break
            if data != "":
                print(data)
                self.distributeMessage(conn, data.encode("utf-8"))
            else:
                self.hostConnections.remove(conn)
                self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" left the chat").encode("utf-8"))
                conn.close()
                break

    def hostSendMessages(self):
        """
        Sends messages to the other connections
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
                    print("\n"+self.name+": "+message)
                    for conn in self.hostConnections:
                        conn.send(("\n"+self.name+"(you): "+message).encode("utf-8"))
            except Exception as e:
                print(e)
                break
    
    def distributeMessage(self, senderConn, data):
        """
        Sends a message to all connections except the sender
        """

        for conn in self.hostConnections:
            if conn != senderConn:
                conn.send(data)

    def connectToChat(self, address: tuple[str, int]):
        """
        Connects to a hosted chat
        """
        self.mw.connect(address)
        threading.Thread(target=self.receiveMessages, args=(), daemon=True).start()
        print(f"\nConnected to chat on {address}\n")
        self.sendMessages()
    
    def sendMessages(self):
        """
        Sends messages to the host
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
                    print("\n"+self.name+": "+message)
                    self.mw.send(("\n"+self.name+": "+message).encode("utf-8"))
            except Exception as e:
                print(e)
                break
   
    
    def receiveMessages(self):
        """
        Receives messages from the host
        """
        while self.active:
            try:
                data = self.mw.receive().decode("utf-8")
            except ConnectionResetError:
                self.close()
                break
            if data != "":
                print("\n"+data)
            elif data == "\nChat ended\n":
                self.close()
                self.active = False
                break

    def close(self):
        self.mw.close()

if __name__ == "__main__":
    name = input("Choose username: ")
    i = input("Host (h) or connect (c)? ")
    if i == "h":
        port = int(input("What port do you want to host on?"))
        service = ChatService(name, ("", port))
        service.hostChat()
    elif i == "c":
        port = int(input("What port do you want to use?"))
        service = ChatService(name, ("", port))
        hostIP = input("Host IP? ")
        hostPort = int(input("Host Port? "))
        if hostIP == "":
            hostIP = "localhost"
        service.connectToChat((hostIP, hostPort))
            



    

