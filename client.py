# client code
from socket import *

# CONTROL CHANNEL
# connect to server

# continuously accept commands from user in a loop
    # promt: ftp>
    # read user input command

    # send command to server (GET <filename>, PUT <filename> <filesize>, LS)

    # wait for server response (OK <filesize/length>, READY, ERROR)
    # if OK
        # get filesize/length

    # if ERROR
        # print error message

    # DATA CHANNEL
    # else if data transfer command (GET <filename>, PUT <filename> <filesize>, LS)
        # create socket
        # OS will assign the ephemeral port # so bind to port 0
        # start listening
        
        # send this port number to the server with PORT <port_number>

        # accept server connection

        # if GET
            # receive until <filesize> bytes have been received
        # if PUT
            # send message until <filesize> bytes have been sent
        # if LS
            # receive until <length> bytes have been received

        # close data channel connection

    # else if user inputs QUIT command
        # send QUIT command to server
        # break loop

# close control channel socket