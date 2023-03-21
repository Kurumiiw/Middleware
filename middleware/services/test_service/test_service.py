from middleware.middlewareAPI import *
import threading
import json

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
        self.workers = []
        self.running = False
        self.unreliable = MiddlewareAPI.unreliable()
        self.reliable = MiddlewareAPI.reliable()

    
    def configure(self, filepath):
        with open(filepath, "r") as f:
            self.config = json.load(f)
        
        # Configure workers
        for worker in self.config["workers"]:
            self.worker.append(Worker(worker))
    
    def run(self):
        pass

    
    





class Worker(threading.Thread):
    """
    Should:
    - Receive and set configuration from Controller.
    - Echo data as well as measured statistics to Controller.
    """
    def __init__(self, config):
        threading.Thread.__init__(self)
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

        if self.reliable:
            self.sock = MiddlewareAPI.reliable("", self.port, self.TOS, self.mtu)
        else:
            self.sock = MiddlewareAPI.unreliable("", self.port, self.TOS, self.mtu)
    
    def run(self):
        self.running = True
        while self.running:
            # Receive data
            # Send data back
            # Send statistics to controller
            pass

if __name__ == "__main__":
    controller = Controller()
    controller.set()
    controller.run()