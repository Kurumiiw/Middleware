from middleware.middlewareAPI import *
import threading


client_1 = MiddlewareAPI.reliable("", 5000, TOS=0x8, MTU=150, timeout=10)
client_2 = MiddlewareAPI.reliable("", 5005, TOS=0x8, MTU=150, timeout=10)

client_2.bind(("", 5005))

def receive():
    client_receive, addr = client_2.accept()
    received_data = client_receive.receive()
    print(received_data)

thr = threading.Thread(target=receive, daemon=True)
thr.start()
client_1.connect(("localhost", 5005))
client_1.send(b"Hello there")

received_data = client_2.receive()
print(received_data)