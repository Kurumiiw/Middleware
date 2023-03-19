import pytest
import threading
from socket import *
from middleware.middlewareAPI import *


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

    max_payload_size = mwSend.get_max_payload_size()
    gif_data_payloads = [gifData[i*max_payload_size:(i+1)*max_payload_size] for i in range(len(gifData)//max_payload_size + int(len(gifData)%max_payload_size != 0))]

    def sendPacket(mwSocket):
        for payload in gif_data_payloads:
            mwSocket.sendto(payload, ("localhost", 5005))

    mwReceive.bind(("", 5005))
    threading.Thread(
        target=sendPacket, args=(mwSend,)
    ).start()  # Send in different thread because receiving buffer is too small to hold the entire file
    payloads_received = []
    for i in range(len(gif_data_payloads)):
        payloads_received.append(mwReceive.recvfrom()[0])

    assert payloads_received.sort() == gif_data_payloads.sort()

    mwReceive.close()
    mwSend.close()

if __name__ == "__main__":
    test_send_and_receive_reliable()
    test_sending_and_receiving_large_file_reliable()
