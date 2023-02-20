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
            data = conn.receive().decode("utf-8")
            if data != "":
                print(data)
                self.distributeMessage(conn, data.encode("utf-8"))
            else:
                self.hostConnections.remove((conn, addr))
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
                        conn.send(("\n"+self.name+": "+message).encode("utf-8"))
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
                    self.mw.send("Chat ended".encode("utf-8"))
                    self.mw.close()
                    exit()
                else:
                    print("\n"+self.name+": "+message)
                    self.mw.send(("\n"+self.name+": "+message).encode("utf-8"))
            except Exception as e:
                print(e)
                break


    # def listenForConnections(self):
    #     self.mw.listen()
    #     while True:
    #         conn, addr = self.mw.accept()
    #         self.hostConnections.append((conn, addr))
    #         print("Connection from "+addr[0]+":"+str(addr[1]))
    #         threading.Thread(target=self.handleConnection, args=(conn, addr), daemon=True).start()
    
    # def handleConnection(self, conn, addr):
    #     while True:
    #         data = conn.receive().decode("utf-8")
    #         if data != "":
    #             print(data)
    #         else:
    #             self.hostConnections.remove((conn, addr))
    #             conn.close()
    #             break

    # def listenForChats(self):
    #     self.mw.listen()
    #     conn, addr = self.mw.accept()
    #     self.hostConnections.append((conn, addr))
    #     threading.Thread(target=self.listenForConnections, args=(conn, addr), daemon=True).start()
    #     self.enterChat(conn)

   
    
    def receiveMessages(self):
        while self.active:
            try:
                data = self.mw.receive().decode("utf-8")
            except ConnectionResetError:
                self.close()
                break
            if data != "":
                # print(data[0] + ": " + data[1])
                print("\n"+data)
            elif data == "\nChat ended\n":
                self.close()
                self.active = False
                break

    def close(self):
        self.mw.close()

if __name__ == "__main__":
    # name = input("What is your name? ")
    # address = (input("What is your IP? "), int(input("What is your port? ")))
    # service = ChatService(name, address)
    # connectOrListen = input("Do you want to connect to a chat or listen for a connection? ")
    # if connectOrListen == "connect":
    #     chatPort = int(input("What is the port of the chat you want to enter? "))
    #     service.connectToChat(("localhost", chatPort))
    # elif connectOrListen == "listen":
    #     service.hostChat()
    # else:
    #     print("Invalid input")
    #     service.close()
    name = input("What is your name? ")
    address = (input("What is your IP? "), int(input("What is your port? ")))
    i = input("h or c? ")
    if i == "h":

        service = ChatService(name, ("", 5000))
        service.hostChat()
    elif i == "c":
        service = ChatService(name, address)
        hostAddress = (input("Host IP? "), int(input("Host Port? ")))
        service.connectToChat(hostAddress)
            



    

