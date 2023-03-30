import sys
import os
from middleware.middlewareAPI import *
import threading
import json
import random
import time

""" 
Configurable test service for sending a lot of random data according to some configuration 
(eg. lots of small packets/a few big packets / reliable/unreliable / burst/regular interval. 
For received data, send back a hash of the data to source to allow for verification. 
Collect statistics about the provided service, and report it.
Should allow for systematic testing of many network patterns, and realistic sending patterns.
"""

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
    def __init__(self):
        self.config = None
        self.workers = {}
        self.connections = {}
        self.running = False
        self.unreliable = MiddlewareUnreliable()
        self.reliable = MiddlewareReliable()


    
    def configure(self, filepath):
        with open(filepath, "r") as f:
            self.config = json.load(f)

        self.reliable.bind(("", 5000))
        self.reliable.listen(len(self.config["workers"]))
        
        # Configure workers
        for worker in self.config["workers"]:
            self.workers[worker["name"]] = Worker(worker)
            conn, _ = self.reliable.accept()
            conn.settimeout(0)
            self.connections[worker["name"]] = conn
        
        print(len(self.workers))
        self.unreliable.bind(("", 5000))
    
    def run_simultaneous(self):
        self.running = True
        for worker in self.workers.values():
            worker.start()
        LINE_BACK = '\033[1A'
        LINE_CLEAR = '\033[2K'
        while any([worker.is_alive() for worker in self.workers.values()]):
            for conn in self.connections.values():
                try:
                    conn.recv(256*256)
                except:
                    pass
            time.sleep(0.01)
            for worker in self.workers.values():
                print(f"Progress {worker.name}: {(worker.total_packets-worker.progress)/worker.total_packets*100:.2f}%")
            print(LINE_BACK*len(self.workers), end=LINE_CLEAR)
        self.running = False

    
    





class Worker(threading.Thread):
    """
    Should:
    - Receive and set configuration from Controller.
    - Echo data as well as measured statistics to Controller.
    """
    def __init__(self, config):

        #Config legend:
        # mtu: Maximum transmission unit
        # name: Name of worker. i.e. "file_transfer" should be named based on analogy to real-world service.
        # TOS: Type of service value
        # reliable: Whether to use reliable or unreliable connection
        # port: Port to listen on

        # packet_size: Size of packets to send
        # packet_size_variance: Variance of packet size. 0.1 means 10% variance

        # send_interval: Interval between sending packets. 0 means send as fast as possible.
        # send_interval_variance: Variance of send interval. 0.1 means 10% variance. Does not apply if send_interval is 0.

        # burst_size: Number of packets to send in a burst. 0 means send packets at regular intervals.
        # burst_size_variance: Variance of burst size. 0.1 means 10% variance. Does not apply if burst_size is 0.

        # burst_interval: Interval between bursts. 0 means send packets as fast as possible.
        # burst_interval_variance: Variance of burst interval. 0.1 means 10% variance. Does not apply if burst_interval is 0.

        # total_packets: Total number of packets to send

        #The difference between send_interval and burst_interval is that send_interval is the interval between sending packets, while burst_interval is the interval between bursts (or groups of packets). If burst_size is 0, then burst_interval is ignored.



        threading.Thread.__init__(self, daemon=True)
        self.mtu = config["mtu"]
        self.name = config["name"]
        self.TOS = config["TOS"]
        self.reliable = config["reliable"]
        self.port = config["port"]

        self.packet_size = config["packet_size"]
        self.packet_size_variance = config["packet_size_variance"]

        self.send_interval = config["send_interval"]
        self.send_interval_variance = config["send_interval_variance"]

        self.burst_size = config["burst_size"]
        self.burst_size_variance = config["burst_size_variance"]
        self.burst_interval = config["burst_interval"]
        self.burst_interval_variance = config["burst_interval_variance"]

        self.total_packets = config["total_packets"]
        self.progress = self.total_packets

        if self.reliable:
            self.sock = MiddlewareReliable()
            self.sock.bind(("", self.port))
            self.sock.connect(("localhost", 5000))
        else:
            self.sock = MiddlewareUnreliable()
            self.sock.bind(("", self.port))
        self.sock.set_tos(self.TOS)

        
        self.statistics = {
            "name": self.name,
            "send_events": [],
            "receive_events": []
        }


    
    def run(self):
        self.running = True

        def send_packet(packet):
            if self.reliable:
                self.sock.send(packet)
            else:
                self.sock.sendto(packet, ("localhost", 5000))
            self.statistics["send_events"].append({
                "time": time.time(),
                "size": len(packet)
            })
        
        #connect to controller

        while self.running:
            packet_size = round(self.packet_size * (1 + random.uniform(-self.packet_size_variance, self.packet_size_variance)))
            send_interval = self.send_interval * (1 + random.uniform(-self.send_interval_variance, self.send_interval_variance))
            burst_size = min(round(self.burst_size * (1 + random.uniform(-self.burst_size_variance, self.burst_size_variance))), self.progress)
            burst_interval = self.burst_interval * (1 + random.uniform(-self.burst_interval_variance, self.burst_interval_variance))

        
            while burst_size > 0:
                packet = random.randbytes(packet_size)
                send_packet(packet)
                burst_size -= 1
                self.progress -= 1
                time.sleep(send_interval/1000)
            time.sleep(burst_interval/1000)
            if self.progress <= 0:
                self.running = False
                self.done = True


if __name__ == "__main__":
    controller = Controller()
    path = os.path.dirname(os.path.realpath(__file__))
    controller.configure(path + "/config.json")
    controller.run_simultaneous()