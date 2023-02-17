from socket import *
from middleware.fragmentation.packet import *
from middleware.fragmentation.fragment import *
import threading
import time
class MiddlewareAPI():

    @staticmethod
    def reliable(ip:str, 
                 port:int, 
                 TOS:int = 0, 
                 MTU:int = 1500, 
                 timeout:float = 0.5, 
                 maxRetries:int = 5
        ) -> "MiddlewareReliable":
        return MiddlewareReliable(ip, port, TOS, MTU, timeout, maxRetries)
    
    @staticmethod
    def unreliable(ip:str, 
                   port:int, 
                   TOS:int = 0, 
                   MTU:int = 1500, 
                   timeout:float = 0.5, 
                   maxRetries:int = 5
        ) -> "MiddlewareUnreliable":
        return MiddlewareUnreliable(ip, port, TOS, MTU, timeout, maxRetries)
    

class MiddlewareReliable():
    def __init__(self,
                  ip:str, 
                  port:int, 
                  TOS:int = 0, 
                  MTU:int = 1500, 
                  timeout:float = 0.5, 
                  maxRetries:int = 5, 
                  sock = None
        ):
        self.ip = ip
        self.port = port
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.maxRetries = maxRetries
        if sock is None:
            self.socko = socket(AF_INET, SOCK_STREAM)
            self.socko.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
            self.socko.settimeout(self.timeout)
        else:
            self.socko = sock
    
    def connect(self, address: tuple[str, int]) -> None:
        self.socko.connect(address)

    def send(self, data: bytes) -> None:
        pack = Packet(data)
        for i in pack.fragment(self.MTU):
            self.socko.send(i.get_data())

    def listen(self, backlog: int = 5) -> None:
        self.socko.listen(backlog)
    
    def bind(self, address: tuple[str, int]) -> None:
        self.socko.bind(address)
    
    def accept(self) -> tuple["MiddlewareReliable", tuple[str, int]]:
        sock, address = self.socko.accept()
        return MiddlewareReliable(*sock.getsockname(), sock=sock), address
    
    @classmethod
    def fromSocket(cls, sock: socket) -> "MiddlewareReliable":
        return cls(sock=sock)
    
    def close(self) -> None:
        """Banishes the socket from the mortal realm"""
        self.socko.close()
    
    def receive(self) -> bytes:
        return self.socko.recv(self.MTU)
    
        
class MiddlewareUnreliable():
    def __init__(
            self, 
            ip:str, 
            port:int, 
            TOS:int = 0, 
            MTU:int = 1500, 
            timeout:float = 0.5, 
            maxRetries:int = 5
        ):
        self.ip = ip
        self.port = port
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.fragmentTimeout = 2 #TODO: Change this with config file
        self.maxRetries = maxRetries
        self.socko = socket(AF_INET, SOCK_DGRAM)
        self.socko.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        self.socko.settimeout(self.timeout)
        self.fragmentsDict = {} # {(address, packetID): [[packets], time]}

    def send(self, 
             data: bytes, 
             address: tuple[str, int]
        ) -> None:
        pack = Packet(data)
        for i in Fragment.fragment(pack, self.MTU):
            self.socko.sendto(i.data, address)

    def bind(self) -> None:
        self.socko.bind((self.ip, self.port))

    def receive(self) -> tuple[bytes, tuple[str, int]]:
        while True:
            data, address = self.socko.recvfrom(self.MTU)
            pack = Fragment.create_from_raw_data(data)

            if not pack.is_fragment(): #Complete packet received
                if self.fragmentsDict: #Check fragments for timeout
                    for i in list(self.fragmentsDict):
                        if self.fragmentsDict[i][1] < time.time() - self.fragmentTimeout:
                            del self.fragmentsDict[i]
                return pack.get_data(), address

            if (address, pack.get_packet_id()) not in self.fragmentsDict: #New fragment
                self.fragmentsDict[(address, pack.get_packet_id())] = [[pack], time.time()]
                #Check other fragments for timeout
                for i in list(self.fragmentsDict):
                    if i[0] == address and i[1] == pack.get_packet_id():
                        continue
                    if self.fragmentsDict[i][1] < time.time() - self.fragmentTimeout:
                        del self.fragmentsDict[i]
            else: #Fragment already in dict
                self.fragmentsDict[(address, pack.get_packet_id())][0].append(pack)
                self.fragmentsDict[(address, pack.get_packet_id())][1] = time.time() #Update timeout time

            if len(self.fragmentsDict[(address, pack.get_packet_id())][0]) == pack.get_last_fragment_number(): #All fragments received
                reassembledPacket = Fragment.reassemble(self.fragmentsDict[(address, pack.get_packet_id())][0])
                del self.fragmentsDict[(address, pack.get_packet_id())]
                return reassembledPacket.get_data(), address

    def bind(self) -> None:
        self.socko.bind((self.ip, self.port))

    def close(self) -> None:
        """Closes the socket and banishes it from the mortal realm (or plane, if you prefer). 
        Use this method to rid your system of any malevolent socket entities and restore order to the world of network programming!
         \- ChatGPT 2023"""
        self.socko.shutdown(SHUT_RDWR)
        self.socko.close()
        


if __name__ == "__main__":
    def sendDelayed():
        time.sleep(4)
        print(mw2.fragmentsDict)
        mw.send(b"Bababoi", ("localhost", 5005))
    mw = MiddlewareAPI.unreliable("", 5000, TOS = 0x8, MTU = 150, timeout=10)
    mw2 = MiddlewareAPI.unreliable("", 5005, TOS = 0x8, MTU = 150, timeout=10)
    mw2.bind()
    mw.bind()
    mw.send(b"Hello there"*80, ("localhost", 5005))
    threading.Thread(target=sendDelayed, daemon=True).start() #Change send to skip one fragment to test timeout
    receivedData = mw2.receive()
    print(receivedData)
    print(mw2.fragmentsDict)
    



    
# if __name__ == "__main__":
#     def test(mwSocket):
#         conn, addr = mwSocket.accept()
#         print(conn)
#         print(conn.receive())
#         conn.send(b"General Kenobi")
#     mw = MiddlewareAPI.reliable("", 5000, TOS = 0x5)
#     mw2 = MiddlewareAPI.reliable("", 5005, TOS = 0x5)
#     mw.bind(("", 5000))
#     mw.listen()
#     threading.Thread(target=test, args=(mw,)).start()
#     mw2.connect(("localhost", 5000))
#     mw2.send(b"Hello there")
#     print(mw2.receive()) 


#     print(mw)
#     mw.close()
#     mw2.close()
