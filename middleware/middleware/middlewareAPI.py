from socket import *
from middleware.fragmentation.packet import *
from middleware.fragmentation.fragment import *
from middleware.fragmentation.fragmenter import Fragmenter
import threading
import time


class InvalidIPException(ValueError):
    """
    Raised when an invalid IP is provided.
    """

    pass


class InvalidPortException(ValueError):
    """
    Raised when an invalid port is provided.
    """

    pass


class InvalidMTUException(ValueError):
    """
    Raised when an invalid MTU is provided.
    """

    pass


class InvalidTOSException(ValueError):
    """
    Raised when an invalid TOS is provided.
    """

    pass


class MiddlewareAPI:
    @staticmethod
    def reliable(
        ip: str,
        port: int,
        TOS: int = 0,
        MTU: int = 1500,
        timeout: float = 0.5,
        maxRetries: int = 5,
    ) -> "MiddlewareReliable":
        MiddlewareAPI.validate_fields(ip, port, MTU, TOS)
        return MiddlewareReliable(ip, port, TOS, MTU, timeout, maxRetries)

    @staticmethod
    def unreliable(
        ip: str,
        port: int,
        TOS: int = 0,
        MTU: int = 1500,
        timeout: float = 0.5,
        maxRetries: int = 5,
    ) -> "MiddlewareUnreliable":
        MiddlewareAPI.validate_fields(ip, port, MTU, TOS)
        return MiddlewareUnreliable(ip, port, TOS, MTU, timeout, maxRetries)

    @staticmethod
    def validate_fields(ip: str, port: int, MTU: int, TOS: int) -> None:
        if ip != "":  # If the IP is not empty, validate it
            try:
                inet_aton(ip)
            except OSError:
                raise InvalidIPException("IP must be a valid IPv4 address")

        if port < 0 or port > 65535:
            raise InvalidPortException("Port must be a valid port number")
        if MTU < 68 or MTU > 65535:
            raise InvalidMTUException("MTU must be a valid MTU number")
        if TOS < 0 or TOS > 255:
            raise InvalidTOSException("TOS must be a valid TOS number")


class MiddlewareReliable:
    def __init__(
        self,
        ip: str,
        port: int,
        TOS: int = 0,
        MTU: int = 1500,
        timeout: float = 0.5,
        maxRetries: int = 5,
        sock=None,
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
        for i in Fragmenter.fragment(pack, self.MTU):
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


class MiddlewareUnreliable:
    def __init__(
        self,
        ip: str,
        port: int,
        TOS: int = 0,
        MTU: int = 1500,
        timeout: float = 0.5,
        maxRetries: int = 5,
    ):
        self.ip = ip
        self.port = port
        self.TOS = TOS
        self.MTU = MTU
        self.timeout = timeout
        self.fragmentTimeout = 2  # TODO: Change this with config file
        self.maxRetries = maxRetries
        self.socko = socket(AF_INET, SOCK_DGRAM)
        self.socko.setsockopt(IPPROTO_IP, IP_TOS, self.TOS)
        self.socko.settimeout(self.timeout)
        self.fragmentsDict = {}  # {(address, packetID): [[packets], time]}

    def send(self, data: bytes, address: tuple[str, int]) -> None:
        pack = Packet(data)
        for i in Fragmenter.fragment(pack, self.MTU):
            self.socko.sendto(i.data, address)

    def bind(self) -> None:
        self.socko.bind((self.ip, self.port))

    def receive(self) -> tuple[bytes, tuple[str, int]]:
        while True:
            data, address = self.socko.recvfrom(self.MTU)
            pack = Fragmenter.create_from_raw_data(data)

            received = Fragmenter.process_packets([pack])

            if len(received) == 1:
                return received[0].get_data(), address

    def close(self) -> None:
        """Closes the socket and banishes it from the mortal realm (or plane, if you prefer).
        Use this method to rid your system of any malevolent socket entities and restore order to the world of network programming!
         \- ChatGPT 2023"""
        self.socko.close()


if __name__ == "__main__":

    def sendDelayed():
        time.sleep(4)
        print(mw2.fragmentsDict)
        mw.send(b"Bababoi", ("localhost", 5005))

    mw = MiddlewareAPI.unreliable("", 5000, TOS=0x8, MTU=150, timeout=10)
    mw2 = MiddlewareAPI.unreliable("", 5005, TOS=0x8, MTU=150, timeout=10)
    mw2.bind()
    mw.bind()
    mw.send(b"Hello there" * 80, ("localhost", 5005))
    threading.Thread(
        target=sendDelayed, daemon=True
    ).start()  # Change send to skip one fragment to test timeout
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
