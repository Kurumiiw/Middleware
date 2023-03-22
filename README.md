# Middleware

## System Architecture

<img src="./documentation_images/ffi_diag_ver_2.png" alt="System architecture diagram" style="width:50%;"/>

As shown in the diagram, the middleware exposes an API which enables sending and receiving a byte stream.
The API is split between endpoints for reliable and unreliable communication.
When using unreliable, the byte stream would then be divided into an ordered list of ”data
packets” (fragments) to fit with the Maximum Transmission Unit (MTU) of the network (shown
as ”Split” and ”Merge” in Figure 2).
To reassemble the fragmented packets at the receiving end, a header is prepended with a unique
identifier when sending, and packets are reordered using this information when receiving (shown
as ”Add header, Number” and ”Remove header, Reorder”).
When reliable communication is used, the byte stream is sent and received using TCP, using the configured
TCP options in the config file. For both the reliable and unreliable configurations
it is also possible to set the timeout for blocking operations, as well as the TOS value, through the API.

## API documentation

Our middleware aims to be equivalent to the Python socket API in the functions it implements, as listed below.

After importing the API, we begin our journey by initializing either a MiddlewareReliable or a MiddlewareUnreliable object.

### MiddlewareAPI.connect(address)

Connect to a remote socket at address. (The format of address depends on the address family — see above.)

If the connection is interrupted by a signal, the method waits until the connection completes, or raise a TimeoutError on timeout, if the signal handler doesn’t raise an exception and the socket is blocking or has a timeout. For non-blocking sockets, the method raises an InterruptedError exception if the connection is interrupted by a signal (or the exception raised by the signal handler).

Raises an auditing event socket.connect with arguments self, address.

### MiddlewareAPI.send(bytes)

Send data to the socket. The socket must be connected to a remote socket. The optional flags argument has the same meaning as for recv() above. Returns the number of bytes sent. Applications are responsible for checking that all data has been sent; if only some of the data was transmitted, the application needs to attempt delivery of the remaining data. For further information on this topic, consult the Socket Programming HOWTO.

### MiddlewareAPI.listen([backlog])

Enable a server to accept connections. If backlog is specified, it must be at least 0 (if it is lower, it is set to 0); it specifies the number of unaccepted connections that the system will allow before refusing new connections. If not specified, a default reasonable value is chosen.

### MiddlewareAPI.bind(address)

Bind the socket to address. The socket must not already be bound. (The format of the address is a tuple: (IP, port))

### MiddlewareAPI.accept()

Accept a connection. The socket must be bound to an address and listening for connections. The return value is a pair (conn, address) where conn is a new socket object usable to send and receive data on the connection, and address is the address bound to the socket on the other end of the connection.

### Example usage

To get started, here is a code snippet to show how to interact with the API and set up basic communication using:
Make sure the import path to middleware.middlewareAPI is correct depending on wherer your project is.

**Unreliable:**

```python
    from middleware.middlewareAPI import *

    mwSend = MiddlewareUnreliable("", 5000)
    mwReceive = MiddlewareUnreliable("", 5005)
    mwReceive.bind()
    mwSend.send(b"Hello", ("localhost", 5005))
    dataReceived = mwReceive.receive()[0]
    mwSend.close()
    mwReceive.close()
    print(dataReceived)
```

**Reliable:**
Reliable communication requires at least two threads to function, since one will need to connect while the other one accepts.

```python
    from middleware.middlewareAPI import *
    import threading
    def waitForPacket(mwSocket):
        conn, addr = mwSocket.accept()
        conn.send(b"General Kenobi")
    mwReceive = MiddlewareAPI.reliable("", 5001)
    mwSend = MiddlewareAPI.reliable("", 5006)
    mwReceive.bind(("", 5001))
    mwReceive.listen()
    threading.Thread(target=waitForPacket, args=(mwReceive,)).start()
    mwSend.connect(("localhost", 5001))
    mwSend.send(b"Hello there")
    received = mwSend.receive()
    print(received)
```

### Configuration options

Currently we support the following configuration options (See an example configuration file in `middleware/middleware/configuration/config.ini`

- _MTU_: Allows setting the Maximum Transmission Unit for the underlying network, to prevent relying on [IP fragmentation](https://datatracker.ietf.org/doc/rfc8900/).
- _TCP Congestion algorithm_: Allows setting the congestion control algorithm used by TCP. Currently we support [cubic](https://en.wikipedia.org/wiki/CUBIC_TCP), [reno](https://datatracker.ietf.org/doc/rfc5681/), [vegas](https://en.wikipedia.org/wiki/TCP_Vegas)`
- [_tcp_frto_](https://www.rfc-editor.org/rfc/rfc5682): Whether to use Forward RTO-Recovery.
- _tcp_reflect_tos_: Whether to reflect the IP ToS field.
- [_tcp_sack_](https://www.rfc-editor.org/rfc/rfc2018): Whether to use selective acknowledgements.
- _fragment_timeout_: How long to wait after receiving the first fragment in a sequence, before discarding due to timeout, if incomplete. Configured in milliseconds.

## Poetry

**Note:** This is not necessary to run the middleware normally, as no dependencies outside the Python standard library are required!

Do the following while in the subfolder `middleware/`

- To install dependencies: `poetry install`
- To activate virtual environment: `poetry shell`
- To add dependencies: `poetry add [-D] X` (Use -D for development dependencies)

```

```
