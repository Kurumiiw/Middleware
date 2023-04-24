import sys
import os
from middleware.middlewareAPI import *
import threading
import json
import random
import time

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
        self.destPort = config["destPort"]
        self.destIP = config["destIP"]

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
            self.sock._socko.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            if self.port != 0:
                self.sock.bind(("", self.port))
                print(f"Worker {self.name} bound to port {self.port} (reliable)")
        else:
            self.sock = MiddlewareUnreliable()
            if self.port != 0:
                print(f"Worker {self.name} bound to port {self.port} (unreliable)")
                self.sock.bind(("", self.port))
            else:
                print(f"Worker {self.name} bound wildcard port (unreliable)")
        self.sock.set_tos(self.TOS)

        
        self.statistics = {
            "name": self.name,
            "send_events": [],
            "receive_events": [],
            "data_bytes": 0,
            "send_bytes": 0,
            "receive_bytes": 0,
        }


    
    def run(self):

        if self.reliable:
            self.sock.connect((self.destIP, self.destPort))

        self.running = True

        def send_packet(packet):
            if self.reliable:
                self.statistics["send_bytes"] += self.sock.send(packet)
            else:
                self.statistics["send_bytes"] += self.sock.sendto(packet, (self.destIP, self.destPort))
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
                print(f"Progress {self.name}: {(self.total_packets-self.progress)/self.total_packets*100:.2f}%                  ", end="\r")
                packet = random.randbytes(packet_size)
                self.statistics["data_bytes"] += packet_size
                send_packet(packet)
                burst_size -= 1
                self.progress -= 1
                time.sleep(send_interval/1000)
            time.sleep(burst_interval/1000)
            if self.progress <= 0:
                print()
                print("Done!")
                self.running = False
                self.done = True

    

if __name__ == "__main__":
        
    filepath = "config.json"
    config = {}
    workers = {}
    with open(filepath, "r") as f:
        config = json.load(f)
    for worker in config["workers"]:
        workers[worker["name"]] = Worker(worker) # This works

    def run_single(worker_name):
        worker = workers[worker_name]
        worker.start()
    
    run_single("emil_issue")
    input("Running...")
