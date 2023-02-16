# with open("middleware\tests\api\among-us-dance.gif", "rb") as testGif:
#     exec(testGif.read())
from middleware.middlewareAPI import *

def test_create_MiddlewareReliable():
    mw = MiddlewareReliable("", 5000)
    assert mw.ip == ""
    assert mw.port == 5000
    assert mw.TOS == 0
    assert mw.MTU == 1500
    assert mw.timeout == 0.5
    assert mw.maxRetries == 5
    assert mw.bufferSize == 1024
    assert mw.socko != None

def test_create_MiddlewareUnreliable():
    mw = MiddlewareUnreliable("", 5000)
    assert mw.ip == ""
    assert mw.port == 5000
    assert mw.TOS == 0
    assert mw.MTU == 1500
    assert mw.timeout == 0.5
    assert mw.maxRetries == 5
    assert mw.bufferSize == 1024
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

    mwReceive = MiddlewareAPI.reliable("", 5000)
    mwSend = MiddlewareAPI.reliable("", 5005)

    mwReceive.bind(("", 5000))
    mwReceive.listen()
    threading.Thread(target=waitForPacket, args=(mwReceive,)).start()

    mwSend.connect(("localhost", 5000))
    mwSend.send(b"Hello there")
    assert mwSend.receive() == b"General Kenobi"

    mwReceive.close()
    mwSend.close()


def test_sending_and_receiving_large_file_reliable():

    testGif = open("./among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()

    def waitForPacket(mwSocket):
        conn, addr = mwSocket.accept()
        allReceivedData = b""
        receivedData = conn.receive()

        while receivedData != b"":
            allReceivedData += receivedData
            receivedData = conn.receive()
        
        assert allReceivedData == gifData

    mwReceive = MiddlewareAPI.reliable("", 5000)
    mwSend = MiddlewareAPI.reliable("", 5005)

    mwReceive.bind(("", 5000))
    mwReceive.listen()
    threading.Thread(target=waitForPacket, args=(mwReceive,)).start()

    mwSend.connect(("localhost", 5000))
    mwSend.send(gifData)

    mwReceive.close()
    mwSend.close()

def test_sending_and_receiving_large_file_unreliable():

    testGif = open("./among-us-dance.gif", "rb")
    gifData = testGif.read()
    testGif.close()

    mwSend = MiddlewareUnreliable("", 5000)
    mwReceive = MiddlewareUnreliable("", 5005)
    mwReceive.timeout = 0
    mwReceive.bind()
    mwSend.send(gifData, ("localhost", 5005))

    allDataReceived = b""
    dataReceived = mwReceive.receive()[0]
    while dataReceived != b"":
        allDataReceived += dataReceived
        dataReceived = mwReceive.receive()[0]

    assert dataReceived == gifData

    mwReceive.close()
    mwSend.close()


if __name__ == "__main__":
    test_create_MiddlewareReliable()
    test_create_MiddlewareUnreliable()
    test_send_and_receive_unreliable()
    test_send_and_receive_reliable()
    test_sending_and_receiving_large_file_reliable()
    test_sending_and_receiving_large_file_unreliable()