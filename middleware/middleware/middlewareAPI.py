from socket import *


class MiddleWareAPI():
    def __init__(self, ip, port, reliable = False, TOS = 0, MTU= 1500, timeout = 0.5, maxRetries = 5, bufferSize = 1024):
        self.ip = ip
        self.port = port
        self.reliable = reliable
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.maxRetries = maxRetries
        self.bufferSize = bufferSize


    def send(self, data: bytes, address: tuple) -> None:
        if self.reliable:
            return self.sendReliable(data, address)
        else:
            return self.sendUnreliable(data, address)
    
    def sendUnreliable(self, data: bytes, address: tuple) -> None:
        sendSocket = socket(AF_INET, SOCK_DGRAM)
        sendSocket.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        sendSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
        sendSocket.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
        sendSocket.settimeout(self.timeout)
        sendSocket.bind((self.ip, self.port))
        sendSocket.sendto(data, address)
    
    def sendReliable(self, data: bytes, address: tuple) -> None:
        sendSocket = socket(AF_INET, SOCK_STREAM)
        sendSocket.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        sendSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
        sendSocket.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
        sendSocket.settimeout(self.timeout)
        sendSocket.bind((self.ip, self.port))
        sendSocket.connect(address)
        sendSocket.send(data)
        sendSocket.close()
    
    def receive(self) -> tuple[bytes, tuple]:
        if self.reliable:
            return self.receiveReliable()
        else:
            return self.receiveUnreliable()
    
    def receiveUnreliable(self) -> tuple[bytes, tuple]:
        receiveSocket = socket(AF_INET, SOCK_DGRAM)
        receiveSocket.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        receiveSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
        receiveSocket.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
        receiveSocket.settimeout(self.timeout)
        receiveSocket.bind((self.ip, self.port))
        data, address = receiveSocket.recvfrom(self.MTU)
        return data, address
    
    def receiveReliable(self) -> tuple[bytes, tuple]:
        receiveSocket = socket(AF_INET, SOCK_STREAM)
        receiveSocket.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        receiveSocket.setsockopt(SOL_SOCKET, SO_RCVBUF, self.bufferSize)
        receiveSocket.setsockopt(SOL_SOCKET, SO_SNDBUF, self.bufferSize)
        receiveSocket.settimeout(self.timeout)
        receiveSocket.bind((self.ip, self.port))
        receiveSocket.listen(1)
        connection, address = receiveSocket.accept()
        data = connection.recv(self.MTU)
        connection.close()
        return data, address

























    def setReliable(self, reliable):
        self.reliable = reliable
    
    def setTOS(self, TOS):
        self.TOS = TOS
    
    def setMTU(self, MTU):
        self.MTU = MTU
    
    def setTimeout(self, timeout):
        self.timeout = timeout

    def setMaxRetries(self, maxRetries):
        self.maxRetries = maxRetries
    
    def setBufferSize(self, bufferSize):
        self.bufferSize = bufferSize