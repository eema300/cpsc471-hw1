# server code
from socket import *

# start server

# outer loop: continuously accept new clients

    # listen for client
    # client requests control connection: accept client

    # CONTROL CHANNEL
    # inner loop: each client has its own loop
    # loop while the client-specific control channel socket is open
        
        # receive client message
        # parse message
        
        # if the message is GET
            # if file exists
                # send OK <filesize>
            # if file does not exist
                # send ERROR 'file does not exist'
        
        # if message is PUT
            # send READY
        
        # if message is LS
            # run the ls command on server side
            # send OK <total length of dir listing>
        
        # if message is PORT
            # store client port

        # DATA CHANNEL
        # if GET, PUT, or LS and client port is stored
            
            # create new socket using client's IP + port number
            # connect to client port
            
            # if GET/LS
                # send until all <filesize/length> bytes sent
            # if PUT
                # receive until all expected <filesize> bytes received
            
            # close data connection
            # clear the stored client port

        # if the message is QUIT
            # close the control connection for this client

# close server