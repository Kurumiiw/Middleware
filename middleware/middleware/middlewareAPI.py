from socket import *
import middleware.fragmentation.fragmentation as _fragmentation
from middleware.configuration.config import config as _config
import collections
import math
import time


class MiddlewareReliable:
    _socko: socket
    _mtu: int
    _mss: int

    def __init__(self, mtu=_config.mtu, *, _internal_socket=None):
        if _internal_socket != None:
            self._socko = _internal_socket
        else:
            self._socko = socket(AF_INET, SOCK_STREAM)

        self._mtu = mtu
        # TODO: Force tcp to not use ip or tcp options when sending data.
        #       This will reduce overhead from 120 bytes to 40
        ip_header_size = 20  # IP_OPTIONS are forced off below
        tcp_header_size = (
            20  # TCP options are only used in SYN,ACK and mss is not affected by this
        )
        self._mss = self._mtu - ip_header_size - tcp_header_size
        self._socko.setsockopt(IPPROTO_TCP, TCP_MAXSEG, self._mss)
        self._socko.setsockopt(IPPROTO_IP, IP_OPTIONS, b"")
        self._socko.setsockopt(
            IPPROTO_TCP, TCP_CONGESTION, _config.congestion_algorithm.encode("utf-8")
        )
        # self._socko.setsockopt(IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO) TODO: is path MTU discovery something we want?

    def bind(self, address: tuple[str, int]) -> None:
        """
        Funtionally identical to Pyton socket.bind
        """
        self._socko.bind(address)

    def listen(self, backlog: int = 5) -> None:
        """
        Funtionally identical to Pyton socket.listen
        """
        self._socko.listen(backlog)

    def connect(self, address: tuple[str, int]) -> None:
        """
        Funtionally identical to Pyton socket.connect
        """
        self._socko.connect(address)

    def accept(self) -> tuple["MiddlewareReliable", tuple[str, int]]:
        """
        Funtionally identical to Pyton socket.accept, except the connection socket is converted to a MiddlewareReliable socket
        """
        socko, address = self._socko.accept()
        return MiddlewareReliable(mtu=self._mtu, _internal_socket=socko), address

    def send(self, data: bytes) -> int:
        """
        Funtionally identical to Pyton socket.send
        """
        return self._socko.send(data)

    def sendall(self, data: bytes) -> None:
        """
        Funtionally identical to Pyton socket.sendall
        """
        self._socko.sendall(data)

    def recv(self, buffer_size: int) -> bytes:
        return self._socko.recv(buffer_size)

    def settimeout(self, timeout_s: float) -> None:
        """
        Sets the current timeout (in seconds) for blocking operations (accept/connect/send/sendall/recv), None signifies an infinite timeout
        """
        self._socko.settimeout(timeout_s)

    def gettimeout(self) -> float:
        """
        Returns the current timeout for blocking operations (accept/connect/send/sendall/recv), None signifies an infinite timeout
        """
        return self._socko.gettimeout()

    def set_tos(self, tos: int) -> None:
        """
        Sets the current TOS value used for outbound packets
        """
        self._socko.setsockopt(IPPROTO_IP, IP_TOS, tos)

    def get_tos(self) -> int:
        """
        Returns the current TOS value used for outbound packets
        """
        return self._socko.getsockopt(IPPROTO_IP, IP_TOS)

    def get_mtu(self) -> int:
        """
        Returns the MTU used by this socket
        """
        return self._mtu

    def get_mss(self) -> int:
        """
        Returns the MSS (Maximum Segment Size, MTU - headers) used by this socket
        """
        return self._mss

    def close(self) -> None:
        """Banishes the socket from the mortal realm"""
        self._socko.close()


class MiddlewareUnreliable:
    _socko: socket
    _fragmenter: _fragmentation.Fragmenter
    _reassembler: _fragmentation.Reassembler
    _mtu: int

    def __init__(self, mtu=_config.mtu):
        self._socko = socket(AF_INET, SOCK_DGRAM)
        # self._socko.setsockopt(IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO) TODO: is path MTU discovery something we want?

        self._fragmenter = _fragmentation.Fragmenter()
        self._reassembler = _fragmentation.Reassembler()
        self._mtu = mtu

    def bind(self, address: tuple[str, int]) -> None:
        """
        Functionally identical to Pyton socket.bind
        """
        self._socko.bind(address)

    def settimeout(self, timeout_s: float) -> None:
        """
        Sets the current timeout (in seconds) for blocking operations (sendto/recvfrom), None signifies an infinite timeout
        """
        self._socko.settimeout(timeout_s)

    def gettimeout(self) -> float:
        """
        Returns the current timeout for blocking operations (sendto/recvfrom), None signifies an infinite timeout
        """
        return self._socko.gettimeout()

    def set_tos(self, tos: int) -> None:
        """
        Sets the current TOS value used for outbound packets
        """
        self._socko.setsockopt(IPPROTO_IP, IP_TOS, tos)

    def get_tos(self) -> int:
        """
        Returns the current TOS value used for outbound packets
        """
        return self._socko.getsockopt(IPPROTO_IP, IP_TOS)

    def get_mtu(self) -> int:
        """
        Returns the MTU used by this socket
        """
        return self._mtu

    def get_mss(self) -> int:
        """
        Returns the MSS (Maximum Segment Size, MTU - headers) used by this socket. This is per underlying udp datagram,
        and is therefore different from the maximum payload that can be sent (indicated by get_max_payload_size()).
        This value is the maximum amount of payload that can be sent with each fragment.
        """
        return (
            self._mtu
            - _fragmentation.UDP_IP_HEADER_SIZE
            - _fragmentation.MW_HEADER_SIZE
        )

    @staticmethod
    def get_max_payload_size() -> int:
        """
        Returns the maximum payload size than can be sent with a single MiddlewareUnrelaible datagram (single call to sendto)
        """
        return _fragmentation.MAX_DGRAM_PAYLOAD

    def close(self) -> None:
        """Closes the socket and banishes it from the mortal realm (or plane, if you prefer).
        Use this method to rid your system of any malevolent socket entities and restore order to the world of network programming!
         - ChatGPT 2023"""
        self._socko.close()

    def sendto(self, data: bytes, address: tuple[str, int]) -> None:
        """
        Mimics Python socket.sendto, but the blocking timeout affects an internal socket.sendto call
        for each fragment sent, and not the MiddlewareUnreliable.sendto call. Rated for max payload of 63488 B
        (this can be queried with MiddlewareUnreliable.get_max_payload_size)
        """
        for fragment in self._fragmenter.fragment(data):
            self._socko.sendto(fragment, address)

    def recvfrom(self) -> tuple[bytes, tuple[str, int]]:
        """
        Mimics Python socket.recvfrom, but "block" until either a timeout error is raised by an internal socket.recvfrom call
        or a complete MiddlewareUnreliable datagram has arrived
        """
        while True:
            # NOTE: Probe received fragment size
            buffer_size = _config.mtu
            while True:
                _, _, msg_flags, _ = self._socko.recvmsg(buffer_size, 0, MSG_PEEK)
                if msg_flags == MSG_TRUNC:
                    buffer_size *= 2
                    continue
                else:
                    break

            frag, _, msg_flags, addr = self._socko.recvmsg(buffer_size)
            assert (msg_flags & MSG_TRUNC) == 0

            # NOTE: Old datagrams (partial/complete datagrams containing old fragments) are timed out after the blocking socket.recvfrom
            #       operation has completed to avoid datagram id collisions when a lot of time is spent in socket.recvfrom
            self._reassembler.timeout_old_datagrams()

            self._reassembler.add_fragment_to_datagram(frag, addr)

            completed_dgram = self._reassembler.check_for_completed_datagrams()
            if completed_dgram == None:
                continue
            else:
                return completed_dgram[0], completed_dgram[1]
