# Middleware

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

    client_1 = MiddlewareAPI.unreliable("", 5000, TOS=0x8, MTU=150, timeout=10)
    client_2 = MiddlewareAPI.unreliable("", 5005, TOS=0x8, MTU=150, timeout=10)
    
    client_2.bind(("", 5005))

    client_1.send(b"Hello there", ("localhost", 5005))
    
    received_data = client_2.receive()
    print(received_data)
```

**Reliable:**
Reliable communication requires at least two threads to function, since one will need to connect while the other one accepts.

```python
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
```

## Poetry

**Note:** This is not necessary to run the middleware normally, as no dependencies outside the Python standard library are required!

Do the following while in the subfolder `middleware/`

- To install dependencies: `poetry install`
- To activate virtual environment: `poetry shell`
- To add dependencies: `poetry add [-D] X` (Use -D for development dependencies)

