import sys
import os
from middleware.middlewareAPI import *
import threading
import json
import random
import time
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

class Controller:
    """
    Should:
    - Load test configuration from config file and configure worker(s).
        - Simple port discovery when connecting to workers.
        - Configuration should support setting a distribution of packet size to send, what type of connection to use (reliable/unreliable) and whether traffic should be spaced evenly or in bursts.
    - Run tests and collect statistics.
    - Reporting of test results
        - RTT, packet lost, retransmission overhead, amount of data received/sent on either end, etc.
        - Console
        - HTML report (??)
     """
    def __init__(self, ip, port):
        self.connections = {}
        self.running = True
        self.unreliable = MiddlewareUnreliable()
        self.reliable = MiddlewareReliable()
        self.reliable.bind((ip, port))
        self.reliable.listen(5)
        self.unreliable.bind((ip, port))

    def run(self):
        def run_reliable():
            def run_conn(conn, addr):
                self.connections[addr] = []
                while True:
                    data = conn.recv(2048)
                    self.connections[addr].append((data, time.time()))
            
            while True:
                print("Ready to connect")
                conn, addr = self.reliable.accept()
                threading.Thread(target=run_conn, args=(conn, addr), daemon=True).start()
                print(f"New connection from {addr}")

        def run_unreliable():
            data, address = self.unreliable.recvfrom()
            if address in self.connections.keys():
                self.connections[address].append((data, time.time()))
            else:
                self.connections[address] = [(data, time.time())]
        
        rel_thread = threading.Thread(target=run_reliable, daemon=True)
        unrel_thread = threading.Thread(target=run_unreliable, daemon=True)
        rel_thread.start()
        unrel_thread.start()


if __name__ == "__main__":
    controller = Controller("", 5001)
    controller.run()
    input()