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
    
    def print_statistics(self, addr = None):
        if addr == None:
            for i in self.connections:
                stats = self.connections[i]
                total_data_len = 0
                for j in stats:
                    total_data_len += len(j[0])
                print(i,":")
                print("Total data", total_data_len)
                print("Average bandwidth:", (total_data_len / (stats[-1][1] - stats[0][1])) * 8)
        else:
            stats = self.connections[addr]
            total_data_len = 0
            for j in stats:
                total_data_len += len(j[0])
            print(addr,":")
            print("Total data:", total_data_len)
            print("Average bandwidth:", (total_data_len / (stats[-1][1] - stats[0][1])) * 8)

    def run(self):
        def run_reliable():
            def run_conn(conn, addr):
                self.connections[addr] = []
                while True:
                    data = conn.recv(2048)
                    self.connections[addr].append((data, time.time()))
                    if data == b"":
                        self.print_statistics(addr)
                        break
            
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