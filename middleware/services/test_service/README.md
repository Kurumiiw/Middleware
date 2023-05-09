# Test service

As part of the project the team developed a test service to be able to test
configurations.

This test service allows testing a specific test pattern over a link, and can
thus be used to tune the middleware for novel configurations.

To run the test service one controller can be connected to 1 or more workers. This is done by running the `controller.py` and `worker.py` file respectively.

## Controller

The controller will receive data from the workers, and report performance data. Currently, it reports the following data:

- The average bandwidth across the link in bits per seconds.

## Worker

A single worker can run multiple configurations in parallel using separate threads. As the service was developed mainly for testing within the team, this requires some clunky manual changes to the code.

In `worker.py`, line 175 can be replaced with one or more `run_single` calls. The name passed to the function call is the name attribute specified in the configuration file.

## Configuration

The test service is configured using the `config.json` file. An example can be seen in `config.json`.

The following options are available:

- **mtu** (int) Sets the MTU used by the middleware ().
- **name** (string) Is used to select which configuration to use in `worker.py`.
- **TOS** (int) Sets the value of the Type-of-Service (TOS) field to be used.
- **reliable** (bool) Sets whether to use reliable communication. Otherwise unreliable will be used.
- **port** (int) The port which the worker should bind to. It can be set to `0` to use a random port.
- **destPort** (int) The port on the controller system which the worker will connect to.
- **destIP** (string) The IP address of the controller system.
- **packet_size** (int) The mean size of packets to send in bytes.
- **packet_size_variance** (float) The variance of packet size.
- **send_interval** (int) The time between sending individual packets in milliseconds.
- **send_interval_variance** (float) The variance in of send interval.
- **burst_size** (int): The number of packets sent in a single burst.
- **burst_size_variance** (float): The variance of burst size.
- **burst_interval** (int) The delay between bursts in milliseconds.
- **burst_interval_variance** (float): The variance of the burst interval.
- **total_packets** (int): The total number of packets to be sent.

Assuming no variance the total amount of data sent is `total_packets*packet_size` in bytes. In case of variance, the expected mean will be equal to this value, but slight variation may occur.
