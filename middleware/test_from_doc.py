from middleware.middlewareAPI import *
import threading

# client_1 = MiddlewareAPI.reliable("", 5000, TOS=0x8, MTU=150, timeout=10)
# client_2 = MiddlewareAPI.reliable("", 5005, TOS=0x8, MTU=150, timeout=10)

# client_2.bind(("", 5005))


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
mwSend.connect(("localhost", 5001))
mwSend.send(b"Hello there")
received = mwSend.receive()
print(received)
