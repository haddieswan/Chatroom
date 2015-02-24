import socket
import signal
import time
import threading
import sys

RECV_SIZE = 1024
HOST = 'localhost'
HEARTBEAT = 5
PORT = 0
USERNAME = ''

def ctrl_c_handler(signum, frame):
    exit(0)

def heartbeat():

    global HOST
    global PORT
    global USERNAME

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall('LIVE')
    time.sleep(.1)
    sock.sendall(USERNAME)
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)

    if reply_code == 'DEAD':
        print description
        sock.close()
        exit(0)

    sock.close()

    time.sleep(HEARTBEAT)
    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    return(0)

def main():

    # give host and port information
    global PORT
    global USERNAME

    if len(sys.argv) < 2:
        print 'usage: python Client.py <PORT NUMBER>'
        exit(1)

    PORT = int(sys.argv[1])

    # basic client socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.send('HELO')
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)

    while (reply_code != 'SUCC') and (reply_code != 'FAIL'):
        userInput = raw_input('>' + description)
        sock.sendall(userInput)
        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)

    if reply_code == 'FAIL':
        print description
        sock.close()
        exit(0)
    else:
        USERNAME = sock.recv(RECV_SIZE)
        sock.close()

    logged_in = True
    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    while logged_in:

        userInput = raw_input(description + '\n>')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall('CMND')
        time.sleep(.1)
        sock.sendall(userInput)
        time.sleep(.1)
        sock.sendall(USERNAME)
        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)

        if reply_code == 'LOGO':
            logged_in = False
        sock.close()

    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, ctrl_c_handler)
    main()

# log in
# remember who you are
# connect and send heartbeat with username every X seconds
# can also connect and send commands with username
# log out means stop sending heartbeats