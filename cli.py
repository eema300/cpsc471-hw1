# Code for the client side of the protocol

import socket
import sys


def sendCommand(sock: socket, command=""):

    data_sent = 0
    while data_sent < len(command):
        data_sent += sock.send(command_message[data_sent:])


def recv(sock: socket, numBytes: int):

    tmpBuff = ""
    buffer = ""
    while len(buffer) < numBytes:
        tmpBuff = sock.recv(numBytes)

        if not tmpBuff:
            break

        buffer += tmpBuff

    return buffer


VALID_COMMANDS = ["ls", "get", "put", "quit"]

# Check that correct number of args were used
if len(sys.argv) != 3:
    raise (
        Exception(
            "Not enough arguments. Two arguments must be supplied in the format of <Server Machine> <Server port>"
        )
    )

server_address = sys.argv[1]
server_port = int(sys.argv[2])

# Create control socket and connect
control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
control_sock.connect((server_address, server_port))

while True:
    command = input("ftp> ").split()
    if command[0] not in VALID_COMMANDS:
        print("Invalid command. Valid commands include: ls, get, and put.")
        continue
    elif command[0] == "quit":
        break

    # Create Data Socket
    data_sock = control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.bind("", 0)

    command_message = f"port {data_sock.getsockname()[1]}"

    sendCommand(control_sock, command_message)

    data_sent = 0

    # get
    if command[0] == "get":
        if len(command) != 2:
            print(f"Too few or too many arguments. Usage: get <filename>")
            continue
        command_message = f"get {command[1]}"
        sendCommand(control_sock, command_message)
    # ls
    elif command[0] == "ls":
        if len(command) > 2:
            print("Too many arguments provided. Usage: ls")
            continue
        command_message = f"ls"
        sendCommand(control_sock, command_message)
    # Put
    else:
        if len(command) != 3:
            print("Too few or too many arguments. Usage: put <filename> <file size>")
            continue
        command_message = f"put {command[1]} {command[2]}"
        sendCommand(control_sock, command_message)

    # Receive OK message
    OkMsg = recv(control_sock, 11).split()

    respLen = OkMsg[1]

    # Receive data for ls and get
    if command[0] != "put":
        data_sock.listen(data_sock.getsockname()[1])
        data = recv(data_sock, int(respLen))

    # Send file for put
    else:
        fileName = command[1]
        fileSize = command[2]
        file = open(fileName, "r").read(fileSize)

        bytesSent = 0

        while bytesSent < len(file):
            bytesSent += data_sock.send(file[bytesSent:])

    data_sock.close()


print(f"CLosing connection to {server_address} on port {server_port}")
control_sock.close()
