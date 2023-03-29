import pytest
import threading
import random
from socket import *
from middleware.middlewareAPI import *
import middleware.fragmentation.fragmentation as fragmentation
from middleware.configuration.config import config


def test_create_MiddlewareReliable():
    mw = MiddlewareReliable()
    assert mw._socko != None


def test_create_MiddlewareUnreliable():
    mw = MiddlewareUnreliable()
    assert mw._socko != None
    assert mw._fragmenter != None
    assert mw._reassembler != None


def test_send_and_receive_unreliable():
    mwSend = MiddlewareUnreliable()
    mwReceive = MiddlewareUnreliable()
    mwReceive.bind(("", 5005))
    mwSend.sendto(b"Hello", ("localhost", 5005))
    dataReceived = mwReceive.recvfrom()[0]
    assert dataReceived == b"Hello"
    mwSend.close()
    mwReceive.close()


def test_send_and_receive_reliable():
    def waitForPacket(mwSocket):
        conn, addr = mwSocket.accept()
        assert conn.recv(1024) == b"Hello there"
        conn.send(b"General Kenobi")
        conn.close()

    mwReceive = MiddlewareReliable()
    mwSend = MiddlewareReliable()

    # Workaround for address already in use error causing failed tests when running pytest
    # multiple times in quick succession.
    mwReceive._socko.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    mwReceive.bind(("", 5001))
    mwReceive.listen()
    thread = threading.Thread(target=waitForPacket, args=(mwReceive,))
    thread.start()

    mwSend.connect(("localhost", 5001))
    mwSend.send(b"Hello there")

    received = mwSend.recv(1024)
    print(received)
    assert received == b"General Kenobi"

    thread.join()
    mwReceive.close()
    mwSend.close()


def test_sending_and_receiving_large_file_reliable():
    testGif = open("tests/api/among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()

    def sendPacket(mwSocket):
        mwSocket.connect(("localhost", 5000))
        mwSocket.sendall(gifData)

    mwReceive = MiddlewareReliable()
    mwSend = MiddlewareReliable()

    mwReceive.bind(("", 5000))
    mwReceive.listen()
    t = threading.Thread(target=sendPacket, args=(mwSend,))
    t.start()

    conn, addr = mwReceive.accept()
    data = bytearray()
    while len(data) < len(gifData):
        data.extend(conn.recv(1024))
    assert data == gifData

    t.join()

    mwReceive.close()
    mwSend.close()


def test_sending_and_receiving_large_file_unreliable():
    mwSend = MiddlewareUnreliable()
    mwReceive = MiddlewareUnreliable()

    testGif = open("tests/api/among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()

    max_payload_size = MiddlewareUnreliable.get_max_payload_size()
    gif_data_payloads = [
        gifData[i * max_payload_size : (i + 1) * max_payload_size]
        for i in range(
            len(gifData) // max_payload_size + int(len(gifData) % max_payload_size != 0)
        )
    ]

    def sendPacket(mwSocket):
        for payload in gif_data_payloads:
            mwSocket.sendto(payload, ("localhost", 5005))

    mwReceive.bind(("", 5005))
    thread = threading.Thread(
        target=sendPacket, args=(mwSend,)
    )  # Send in different thread because receiving buffer is too small to hold the entire file
    thread.start()

    payloads_received = []
    for i in range(len(gif_data_payloads)):
        payloads_received.append(mwReceive.recvfrom()[0])

    assert payloads_received.sort() == gif_data_payloads.sort()

    thread.join()
    mwReceive.close()
    mwSend.close()


def test_mtu_mss_reliable():
    sock_0 = MiddlewareReliable()
    sock_1 = MiddlewareReliable(mtu=config.mtu - 4)

    tcp_ip_header_size = 40
    assert sock_0.get_mtu() == config.mtu
    assert sock_0.get_mss() == config.mtu - tcp_ip_header_size
    assert sock_1.get_mtu() == (config.mtu - 4)
    assert sock_1.get_mss() == (config.mtu - 4) - tcp_ip_header_size

    sock_0.close()
    sock_1.close()

    sender = MiddlewareReliable()
    receiver = MiddlewareReliable(mtu=config.mtu - 4)

    receiver.bind(("", 6999))
    receiver.listen()

    def connect():
        sender.connect(("localhost", 6999))

    thread = threading.Thread(target=connect, args=())
    thread.start()

    conn, addr = receiver.accept()
    assert conn.get_mtu() == receiver.get_mtu()
    assert conn.get_mss() == receiver.get_mss()

    thread.join()
    receiver.close()
    sender.close()


def test_mtu_mss_unreliable():
    sock_0 = MiddlewareUnreliable()
    sock_1 = MiddlewareUnreliable(mtu=1024)

    total_header_size = fragmentation.UDP_IP_HEADER_SIZE + fragmentation.MW_HEADER_SIZE
    assert sock_0.get_mtu() == config.mtu
    assert sock_0.get_mss() == config.mtu - total_header_size
    assert sock_1.get_mtu() == 1024
    assert sock_1.get_mss() == 1024 - total_header_size

    sock_0.close()
    sock_1.close()


def test_tos_unreliable():
    receiver = MiddlewareUnreliable()
    sender = MiddlewareUnreliable()

    assert sender.get_tos() == 0
    sender.set_tos(6)
    assert sender.get_tos() == 6

    # TODO: inspect tos field of received segments

    receiver.close()
    sender.close()


def test_tos_reliable():
    receiver = MiddlewareReliable()
    sender = MiddlewareReliable()

    assert sender.get_tos() == 0
    sender.set_tos(88)
    assert sender.get_tos() == 88

    # TODO: inspect tos field of received segments

    receiver.close()
    sender.close()


@pytest.mark.slow
def test_settimeout_unreliable():
    sock = MiddlewareUnreliable()
    sock.bind(("", 9000))

    # TODO: also test send

    sock.settimeout(0)
    assert sock.gettimeout() == 0
    with pytest.raises(BlockingIOError):
        sock.recvfrom()

    for i in range(1, 4):
        timeout = 0.5 * i
        sock.settimeout(timeout)
        assert sock.gettimeout() == timeout

        start = time.perf_counter()
        with pytest.raises(TimeoutError):
            sock.recvfrom()

        end = time.perf_counter()

        assert abs((end - start) - timeout) <= timeout

    sock.close()


@pytest.mark.slow
def test_settimeout_reliable():
    # TODO: Also test connect, send and receive
    receiver = MiddlewareReliable()
    receiver.bind(("", 9000))
    receiver.listen()

    receiver.settimeout(0)
    assert receiver.gettimeout() == 0
    with pytest.raises(BlockingIOError):
        receiver.accept()

    for i in range(1, 4):
        timeout = 0.5 * i
        receiver.settimeout(timeout)
        assert receiver.gettimeout() == timeout

        start_accept = time.perf_counter()
        with pytest.raises(TimeoutError):
            receiver.accept()

        end_accept = time.perf_counter()

        assert abs((end_accept - start_accept) - timeout) <= timeout

    receiver.close()
