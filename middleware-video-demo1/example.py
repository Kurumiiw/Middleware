from middleware.middlewareAPI import *

mwSend = MiddlewareUnreliable()
mwReceive = MiddlewareUnreliable()

mwReceive.bind(("", 5005))


mwSend.sendto(b"Hello", ("localhost", 5005))


dataReceived = mwReceive.recvfrom()[0]

print(dataReceived)
mwSend.close()
mwReceive.close()