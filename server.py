# server code
from socket import *
import os
import subprocess
import sys


# Helper Function
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

def send_bytes(sock, data):
    """Send all bytes, looping until complete."""
    total = 0
    while total < len(data):
        sent = sock.send(data[total:])
        if sent == 0:
            raise RuntimeError("Socket closed unexpectedly")
        total += sent

def recv_bytes(sock, size):
    """Receive exactly `size` bytes, looping until complete."""
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(min(4096, size - len(buf)))
        if not chunk:
            break
        buf += chunk
    return buf

if len(sys.argv) != 2:
    print("Usage: python server.py <port>")
    sys.exit(1)

port = int(sys.argv[1])

# start server
server_sock = socket(AF_INET, SOCK_STREAM)
server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
server_sock.bind(("", port))
server_sock.listen(5)
print(f"Server listening on port {port} ...")

# Using try for a cleaner close
try:
    # outer loop: continuously accept new clients
    while True:

        # listen for client
        # client requests control connection: accept client
        ctrl_sock, addr = server_sock.accept()
        client_ip = addr[0]
        print(f"[+] Client connected: {addr}")

        # state tracked per client
        client_port   = None   # set when PORT message arrives
        pending_cmd   = None   # which command is waiting for data transfer
        pending_args  = None   # file name / listing associated with that command

        # CONTROL CHANNEL
        # inner loop: each client has its own loop
        # loop while the client-specific control channel socket is open
        while True:

            # receive client message
            msg = recv_msg(ctrl_sock)
            if not msg:
                print(f"[-] Client {addr} disconnected.")
                break

            # parse message
            parts = msg.split()
            cmd   = parts[0].upper()

            # if the message is GET
            if cmd == "GET":
                filename = parts[1]
                # if file exists
                if os.path.isfile(filename):
                    # send OK <filesize>
                    filesize = os.path.getsize(filename)
                    send_msg(ctrl_sock, f"OK {filesize}\n")
                    pending_cmd  = "GET"
                    pending_args = filename
                # if file does not exist
                else:
                    # send ERROR 'file does not exist'
                    send_msg(ctrl_sock, f"ERROR file does not exist: {filename}\n")

            # if message is PUT
            elif cmd == "PUT":
                filename = parts[1]
                filesize = int(parts[2])
                # send READY
                send_msg(ctrl_sock, "READY\n")
                pending_cmd  = "PUT"
                pending_args = (filename, filesize)

            # if message is LS
            elif cmd == "LS":
                # run the ls command on server side
                result  = subprocess.run(["ls"], capture_output=True, text=True)
                listing = result.stdout
                # send OK <total length of dir listing>
                send_msg(ctrl_sock, f"OK {len(listing.encode())}\n")
                pending_cmd  = "LS"
                pending_args = listing

            # if message is PORT
            elif cmd == "PORT":
                # store client port
                client_port = int(parts[1])

            # DATA CHANNEL
            # if GET, PUT, or LS and client port is stored
            if pending_cmd in ("GET", "PUT", "LS") and client_port is not None:

                # create new socket using client's IP + port number
                # connect to client port
                data_sock = socket(AF_INET, SOCK_STREAM)
                data_sock.connect((client_ip, client_port))

                # if GET/LS
                if pending_cmd == "GET":
                    # send until all <filesize/length> bytes sent
                    with open(pending_args, "rb") as f:
                        payload = f.read()
                    send_bytes(data_sock, payload)
                    print(f"[>] GET  '{pending_args}' – sent {len(payload)} bytes")

                elif pending_cmd == "LS":
                    # send until all <filesize/length> bytes sent
                    send_bytes(data_sock, pending_args.encode())
                    print(f"[>] LS   – sent {len(pending_args)} bytes")

                # if PUT
                elif pending_cmd == "PUT":
                    # receive until all expected <filesize> bytes received
                    filename, filesize = pending_args
                    payload = recv_bytes(data_sock, filesize)
                    with open(filename, "wb") as f:
                        f.write(payload)
                    print(f"[<] PUT  '{filename}' – received {len(payload)} bytes")

                # close data connection
                data_sock.close()

                # clear the stored client port
                client_port  = None
                pending_cmd  = None
                pending_args = None

            # if the message is QUIT
            if cmd == "QUIT":
                # close the control connection for this client
                print(f"[-] Client {addr} quit.")
                ctrl_sock.close()
                break
# When pressing CTRL+C the server closes smoothly                
except KeyboardInterrupt:
    print("\nSERVER IS NOW CLOSING(CTRL+C)")

# close server
finally:
    # Cleaner Close
    try:
        server_sock.close()
    except:
        pass
    # Final Message Goodbye
    print("Server is Closed. Goodbye.")