# client code
from socket import *
import os
import sys

# Helper Functions
def send_msg(sock, msg):
    """Send a complete message, looping until all bytes are sent."""
    data = msg.encode()
    total = 0
    while total < len(data):
        sent = sock.send(data[total:])
        if sent == 0:
            raise RuntimeError("Socket closed unexpectedly")
        total += sent

def recv_msg(sock):
    """Receive a newline-terminated message from the socket."""
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            return ""
        buf += chunk
    return buf.decode().strip()

def recv_bytes(sock, size):
    """Receive exactly `size` bytes, looping until complete."""
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(min(4096, size - len(buf)))
        if not chunk:
            break
        buf += chunk
    return buf

if len(sys.argv) != 3:
    print("Usage: python client.py <server> <port>")
    sys.exit(1)

server_addr = sys.argv[1]
server_port = int(sys.argv[2])

# CONTROL CHANNEL
# connect to server
ctrl_sock = socket(AF_INET, SOCK_STREAM)
ctrl_sock.connect((server_addr, server_port))
print(f"Connected to {server_addr}:{server_port}")

# continuously accept commands from user in a loop
while True:

    # prompt: ftp>
    # read user input command
    try:
        parts = input("ftp> ").strip().split()
    except (EOFError, KeyboardInterrupt):
        break

    if not parts:
        continue

    cmd = parts[0].lower()

    # else if user inputs QUIT command
    if cmd == "quit":
        # send QUIT command to server
        send_msg(ctrl_sock, "QUIT\n")
        # break loop
        break

    # send command to server (GET <filename>, PUT <filename> <filesize>, LS)
    if cmd == "get":
        if len(parts) != 2:
            print("Usage: get <filename>")
            continue
        send_msg(ctrl_sock, f"GET {parts[1]}\n")

    elif cmd == "put":
        if len(parts) != 2:
            print("Usage: put <filename>")
            continue
        if not os.path.isfile(parts[1]):
            print(f"Error: '{parts[1]}' not found locally.")
            continue
        filesize = os.path.getsize(parts[1])
        send_msg(ctrl_sock, f"PUT {parts[1]} {filesize}\n")

    elif cmd == "ls":
        send_msg(ctrl_sock, "LS\n")

    else:
        print("Invalid command. Valid commands: get, put, ls, quit")
        continue

    # wait for server response (OK <filesize/length>, READY, ERROR)
    response = recv_msg(ctrl_sock)
    resp_parts = response.split(None, 1)
    status = resp_parts[0].upper()

    # if OK
    if status == "OK":
        # get filesize/length
        transfer_size = int(resp_parts[1])

    # if ERROR
    elif status == "ERROR":
        # print error message
        print(f"Server error: {resp_parts[1] if len(resp_parts) > 1 else ''}")
        continue

    # DATA CHANNEL
    # else if data transfer command (GET <filename>, PUT <filename> <filesize>, LS)
    if cmd in ("get", "put", "ls"):

        # create socket
        data_sock = socket(AF_INET, SOCK_STREAM)

        # OS will assign the ephemeral port # so bind to port 0
        data_sock.bind(("", 0))
        data_port = data_sock.getsockname()[1]

        # start listening
        data_sock.listen(1)

        # send this port number to the server with PORT <port_number>
        send_msg(ctrl_sock, f"PORT {data_port}\n")

        # accept server connection
        conn, _ = data_sock.accept()

        # if GET
        if cmd == "get":
            # receive until <filesize> bytes have been received
            payload = recv_bytes(conn, transfer_size)
            with open(parts[1], "wb") as f:
                f.write(payload)
            print(f"Received '{parts[1]}': {len(payload)} bytes")

        # if PUT
        elif cmd == "put":
            # send message until <filesize> bytes have been sent
            with open(parts[1], "rb") as f:
                payload = f.read()
            total = 0
            while total < len(payload):
                sent = conn.send(payload[total:])
                if sent == 0:
                    raise RuntimeError("Data socket closed unexpectedly")
                total += sent
            print(f"Sent '{parts[1]}': {total} bytes")

        # if LS
        elif cmd == "ls":
            # receive until <length> bytes have been received
            listing = recv_bytes(conn, transfer_size)
            print(listing.decode(), end="")

        # close data channel connection
        conn.close()
        data_sock.close()

# close control channel socket
print(f"Closing connection to {server_addr}:{server_port}")
ctrl_sock.close()