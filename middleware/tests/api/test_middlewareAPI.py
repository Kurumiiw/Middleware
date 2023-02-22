import pytest
from socket import *
from middleware.middlewareAPI import *


def test_create_MiddlewareReliable():
    mw = MiddlewareReliable("", 5000)
    assert mw.ip == ""
    assert mw.port == 5000
    assert mw.TOS == 0
    assert mw.MTU == 1500
    assert mw.timeout == 0.5
    assert mw.maxRetries == 5
    assert mw.socko != None


def test_create_MiddlewareUnreliable():
    mw = MiddlewareUnreliable("", 5000)
    assert mw.ip == ""
    assert mw.port == 5000
    assert mw.TOS == 0
    assert mw.MTU == 1500
    assert mw.timeout == 0.5
    assert mw.maxRetries == 5
    assert mw.socko != None


def test_send_and_receive_unreliable():
    mwSend = MiddlewareUnreliable("", 5000)
    mwReceive = MiddlewareUnreliable("", 5005)
    mwReceive.bind()
    mwSend.send(b"Hello", ("localhost", 5005))
    dataReceived = mwReceive.receive()[0]
    assert dataReceived == b"Hello"
    mwSend.close()
    mwReceive.close()


def test_send_and_receive_reliable():
    def waitForPacket(mwSocket):
        conn, addr = mwSocket.accept()
        assert conn.receive() == b"Hello there"
        conn.send(b"General Kenobi")

    mwReceive = MiddlewareAPI.reliable("", 5001)
    mwSend = MiddlewareAPI.reliable("", 5006)

    # Workaround for address already in use error causing failed tests when running pytest
    # multiple times in quick succession.
    mwReceive.socko.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    mwReceive.bind(("", 5001))
    mwReceive.listen()
    threading.Thread(target=waitForPacket, args=(mwReceive,)).start()
    receiveThread = threading.Thread(target=waitForPacket, args=(mwReceive,))
    receiveThread.start()

    mwSend.connect(("localhost", 5001))
    mwSend.send(b"Hello there")
    assert mwSend.receive() == b"General Kenobi"
    receiveThread.join()

    mwReceive.close()
    mwSend.close()


@pytest.mark.slow
def test_sending_and_receiving_large_file_reliable():
    testGif = open("tests/api/among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()
    print("RUNNING TEST")

    def waitForPacket(mwSocket):
        conn, addr = mwSocket.accept()
        allReceived = b""
        st = time.time()
        while allReceived == b"":
            allReceived += conn.receive()
            if time.time() - st > 15:
                break
        assert allReceived == gifData

    mwReceive = MiddlewareAPI.reliable("", 55000)
    mwSend = MiddlewareAPI.reliable("", 5005)

    mwReceive.bind(("", 55000))
    mwReceive.listen()
    receiveThread = threading.Thread(target=waitForPacket, args=(mwReceive,), daemon=True)
    receiveThread.timeout = 15
    receiveThread.start()
    print("RECVTRHEAD STARTED")

    mwSend.connect(("localhost", 55000))
    print("Connected")
    mwSend.send(gifData)
    print("Sent")
    # receiveThread.join()
    time.sleep(20)
    mwReceive.close()
    mwSend.close()



@pytest.mark.slow
def test_sending_and_receiving_large_file_unreliable():
    testGif = open("tests/api/among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()

    def sendPacket(mwSocket):
        mwSocket.send(gifData, ("localhost", 5005))

    mwSend = MiddlewareUnreliable("", 5000)
    mwReceive = MiddlewareUnreliable("", 5005, timeout=15)
    mwReceive.bind()
    sendThread = threading.Thread(
        target=sendPacket, args=(mwSend,)
    ) # Send in different thread because receiving buffer is too small to hold the entire file
    sendThread.start()
    dataReceived = mwReceive.receive()[0]
    sendThread.join()

    assert dataReceived == gifData

    mwReceive.close()
    mwSend.close()

if __name__ == "__main__":
    test_sending_and_receiving_large_file_reliable()