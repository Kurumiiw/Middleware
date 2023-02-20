from middleware.middlewareAPI import *

class ChatService():

    def __init__(self, name: str, address: tuple[str, int]):

        # self.templateClients = [("Ola", "", 5001), ("Thorbjørn", "", 5002), ("Tobias", "", 5003), ("Simon", "", 5004)]
        self.address = address
        self.name = name
        self.mw = MiddlewareAPI.reliable(address[0], address[1], timeout=None)
        self.mw.bind(self.address)
        self.active = True
        

    def listenForChats(self):
        self.mw.listen()
        conn, addr = self.mw.accept()
        self.enterChat(conn)

        # while True:
        #     conn, addr = self.mw.accept()
        #     data = conn.receive()
        #     if data != b"":
        #         print(data[0] + ": " + data[1])
    
    def connectToChat(self, address: tuple[str, int]):
        self.mw.connect(address)
        self.enterChat(self.mw)
        
    
    def enterChat(self, chatmw):
        chatmw.send(("\n"+self.name+" has entered the chat\n").encode("utf-8"))
        print("\nYou have entered the chat\n")
        threading.Thread(target=self.receiveMessages, args=(chatmw,), daemon=True).start()
        while True:
            message = input()
            if not self.active:
                print("Chat ended")
                exit()
            try:
                if message == "exit":
                    chatmw.send(("\nChat ended\n").encode("utf-8"))
                    print("\nChat ended\n")
                    self.close()
                    break
                chatmw.send(("\n"+self.name+": "+message+"\n").encode("utf-8"))
                print("\nYou: "+message+"\n")
            except OSError:
                self.close()
                break
            
    
    def receiveMessages(self, mw):
        while self.active:
            try:
                data = mw.receive().decode("utf-8")
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
    name = input("What is your name? ")
    address = (input("What is your IP? "), int(input("What is your port? ")))
    service = ChatService(name, address)
    connectOrListen = input("Do you want to connect to a chat or listen for a connection? ")
    if connectOrListen == "connect":
        chatPort = int(input("What is the port of the chat you want to enter? "))
        service.connectToChat(("localhost", chatPort))
    elif connectOrListen == "listen":
        service.listenForChats()
    else:
        print("Invalid input")
        service.close()
            



    

