# cpsc471-hw1

## Group Members
- Eddie Cortes (eccortes@csu.fullerton.edu)
- Quentin Rivest (queriv47x@csu.fullerton.edu)
- Josh Navarro
- Emma Gomez (emmanicolego@csu.fullerton.edu)
- Ngoc Tran (ntran562@csu.fullerton.edu)

## Language
Python 3

## How to Run

**Start the server:**
```
python server.py <port>
```
Example: `python server.py 1234`

**Start the client (in a separate terminal):**
```
python client.py <server> <port>
```
Example: `python cli.py localhost 1234`

**Client commands once connected:**
```
ftp> ls                        # list files on the server
ftp> get <filename>            # download a file from the server
ftp> put <filename>            # upload a local file to the server
ftp> quit                      # disconnect and exit
```

---

## Protocol Design

Two TCP connections are used per FTP session.

### Control Channel
Opened when the client starts and stays open for the entire session.
Used exclusively for commands and status messages.
All messages are UTF-8 strings terminated with `\n`.

**Client → Server messages:**
| Message | Description |
|---|---|
| `GET <filename>` | Request a file download |
| `PUT <filename> <filesize>` | Initiate a file upload |
| `LS` | Request directory listing |
| `PORT <port>` | Tell server which ephemeral port to connect to |
| `QUIT` | End the session |

**Server → Client messages:**
| Message | Description |
|---|---|
| `OK <size>` | Command accepted; `size` = bytes the client will receive |
| `READY` | Server is ready to receive a PUT upload |
| `ERROR <message>` | Command failed; reason included |

### Data Channel
Opened and torn down for every transfer (ls, get, put).

**Setup sequence:**
1. Client sends command (`GET`, `PUT`, or `LS`) on the control channel.
2. Server replies `OK <size>` or `READY` (or `ERROR`).
3. Client binds a new socket to an OS-assigned ephemeral port and starts listening.
4. Client sends `PORT <port>` on the control channel.
5. Server connects to the client's IP + that port.
6. Data flows over the new connection until all bytes are transferred.
7. Both sides close the data socket.

**Data flow direction:**
- `GET` / `LS` → Server sends to Client
- `PUT` → Client sends to Server

### Reliable Send / Receive
Both `send_bytes` and `recv_bytes` loop until exactly the expected number of bytes
have been sent or received, handling partial sends/receives caused by TCP segmentation
or buffer limits.