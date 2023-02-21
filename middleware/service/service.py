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
        self.mw.listen()
        print(f"\nWaiting for connections on {self.address}...\n")
        conn, addr = self.mw.accept()
        self.hostConnections.append((conn, addr))
        threading.Thread(target=self.listenForConnections, daemon=True).start()
        threading.Thread(target=self.handleConnection, args=(conn, addr), daemon=True).start()
        self.hostSendMessages()
        

    def listenForConnections(self):
        while True:
            self.mw.listen()
            conn, addr = self.mw.accept()
            self.hostConnections.append((conn, addr))
            threading.Thread(target=self.handleConnection, args=(conn, addr), daemon=True).start()

    def handleConnection(self, conn, addr):
        self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" joined the chat").encode("utf-8"))
        print(f"\n{addr[0]}:{addr[1]} joined the chat\n")
        while True:
            try:
                data = conn.receive().decode("utf-8")
            except ConnectionResetError:
                self.hostConnections.remove((conn, addr))
                self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" left the chat").encode("utf-8"))
                conn.close()
                break
            if data != "":
                print(data)
                self.distributeMessage(conn, data.encode("utf-8"))
            else:
                self.hostConnections.remove((conn, addr))
                self.distributeMessage(conn, ("\n"+addr[0]+":"+str(addr[1])+" left the chat").encode("utf-8"))
                conn.close()
                break

    def hostSendMessages(self):
        while True:
            message = input()
            if not self.active:
                print("Chat ended")
                exit()
            try:
                if message == "exit":
                    self.active = False
                    for conn, addr in self.hostConnections:
                        conn.send("Chat ended".encode("utf-8"))
                        conn.close()
                    self.mw.close()
                    exit()
                else:
                    print("\n"+self.name+": "+message)
                    for conn, addr in self.hostConnections:
                        conn.send(("\n"+self.name+"(you): "+message).encode("utf-8"))
            except Exception as e:
                print(e)
                break
    
    def distributeMessage(self, senderConn, data):
        for conn, addr in self.hostConnections:
            if conn != senderConn:
                conn.send(data)

    def connectToChat(self, address: tuple[str, int]):
        self.mw.connect(address)
        threading.Thread(target=self.receiveMessages, args=(), daemon=True).start()
        print(f"\nConnected to chat on {address}\n")
        self.sendMessages()
    
    def sendMessages(self):
        while True:
            message = input()
            if not self.active:
                print("Chat ended")
                exit()
            try:
                if message == "exit":
                    self.active = False
                    self.mw.send(f"{self.address} left the chat".encode("utf-8"))
                    self.mw.close()
                    exit()
                else:
                    print("\n"+self.name+": "+message)
                    self.mw.send(("\n"+self.name+": "+message).encode("utf-8"))
            except Exception as e:
                print(e)
                break
   
    
    def receiveMessages(self):
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
    name = input("What is your name? ")
    i = input("Host (h) or connect (c)? ")
    if i == "h":
        port = int(input("What port do you want to host on?"))
        service = ChatService(name, ("", port))
        service.hostChat()
    elif i == "c":
        port = int(input("What port do you want to use?"))
        service = ChatService(name, ("", port))
        hostAddress = (input("Host IP? "), int(input("Host Port? ")))
        service.connectToChat(hostAddress)
            



    

