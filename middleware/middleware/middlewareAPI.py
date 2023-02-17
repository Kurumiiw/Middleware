from socket import *
from middleware.fragmentation.packet import *
from middleware.fragmentation.fragment import *
import threading
class MiddlewareAPI():

    @staticmethod
    def reliable(ip, port, TOS = 0, MTU= 1500, timeout = 0.5, maxRetries = 5, bufferSize = 1024):
        return MiddlewareReliable(ip, port, TOS, MTU, timeout, maxRetries, bufferSize)
    
    @staticmethod
    def unreliable(ip, port, TOS = 0, MTU= 1500, timeout = 0.5, maxRetries = 5, bufferSize = 1024):
        return MiddlewareUnreliable(ip, port, TOS, MTU, timeout, maxRetries, bufferSize)
    

class MiddlewareReliable():
    def __init__(self, ip, port, TOS = 0, MTU= 1500, timeout = 0.5, maxRetries = 5, bufferSize = 1024, sock = None):
        self.ip = ip
        self.port = port
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.maxRetries = maxRetries
        self.bufferSize = bufferSize
        if sock is None:
            self.socko = socket(AF_INET, SOCK_STREAM)
            self.socko.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
            self.socko.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
            self.socko.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
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
    def __init__(self, ip:str, port:int, TOS:int = 0, MTU:int = 1500, timeout:float = 0.5, maxRetries:int = 5, bufferSize:int = 1024):
        self.ip = ip
        self.port = port
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.maxRetries = maxRetries
        self.bufferSize = bufferSize
        self.socko = socket(AF_INET, SOCK_DGRAM)
        self.socko.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        self.socko.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
        self.socko.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
        self.socko.settimeout(self.timeout)
        self.fragmentsDict = {}

    def send(self, data: bytes, address: tuple[str, int]) -> None:
        pack = Packet(data)
        for i in Fragment.fragment(pack, self.MTU):
            print(i.data)
            self.socko.sendto(i.data, address)

    def bind(self) -> None:
        self.socko.bind((self.ip, self.port))

    def receive(self) -> tuple[bytes, tuple[str, int]]:
        #TODO: Implement a timeout
        while True:
            data, address = self.socko.recvfrom(self.MTU)
            print(data)
            
            ### Replace this with a built in function of packet
            if int.from_bytes(data[0:4], byteorder="little", signed=False) == 0:
                print("Complete packet received")
                return data, address
            else: 
                print("Fragment received")
                pack = Fragment(b"a", 1, 1, 1)
                pack.data = data


            if (address, pack.get_packet_id()) not in self.fragmentsDict:
                self.fragmentsDict[(address, pack.get_packet_id())] = [pack]
                print(f"Fragment {pack.get_fragment_number()} received. Total fragments: {len(self.fragmentsDict[(address, pack.get_packet_id())])}")
            else:
                self.fragmentsDict[(address, pack.get_packet_id())].append(pack)
                print(f"Fragment {pack.get_fragment_number()} received. Total fragments: {len(self.fragmentsDict[(address, pack.get_packet_id())])}")

            if len(self.fragmentsDict[(address, pack.get_packet_id())]) == pack.get_last_fragment_number():
                print("All fragments received. Reassembling...")
                print(f"Total fragments: {len(self.fragmentsDict[(address, pack.get_packet_id())])}")

                reassembledPacket = Fragment.reassemble(self.fragmentsDict[(address, pack.get_packet_id())])
                del self.fragmentsDict[(address, pack.get_packet_id())]
                print("Reassembled packet")
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
    mw = MiddlewareAPI.unreliable("", 5000, TOS = 0x8, MTU = 150, timeout=10, bufferSize=1024*10)
    mw2 = MiddlewareAPI.unreliable("", 5005, TOS = 0x8, MTU = 150, timeout=10, bufferSize=1024*10)
    mw2.bind()
    mw.bind()
    mw.send(b"Hello there"*80, ("localhost", 5005))
    receivedData = mw2.receive()
    print(receivedData)
    



    
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
