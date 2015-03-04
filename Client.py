from multiprocessing import Lock
import socket
import signal
import time
import threading
import sys

RECV_SIZE = 1024
HOST = 'localhost'
CLIENTHOST = ''
CLIENTPORT = 0
HEARTBEAT = 5
PORT = 0
USERNAME = ''
lock = Lock()

def ctrl_c_handler(signum, frame):
    exit(0)

def serve_client(connection):
    global lock

    message = connection.recv(RECV_SIZE)
    lock.acquire()
    try:
        sys.stdout.write(message + '\n>')
        sys.stdout.flush()
    finally:
        lock.release()
    connection.close()
    return(0)

def listener_thread(client_sock):

    while True:
        conn, addr = client_sock.accept()
        server = threading.Thread(target=serve_client, args=(conn,))
        server.start()

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

    # if reply_code == 'DEAD':
    #     print description
    #     sock.close()
    #     exit(0)

    sock.close()

    time.sleep(HEARTBEAT)
    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    return(0)

def main():

    # give host and port information
    global PORT
    global HOST
    global USERNAME
    global CLIENTHOST
    global CLIENTPORT

    if len(sys.argv) < 3:
        print 'usage: python Client.py <IP ADDRESS> <PORT NUMBER>'
        exit(1)

    start_port = 8000
    while True:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = client_sock.bind((HOST, start_port))
            client_sock.listen(1)
            CLIENTPORT = start_port
            break
        except Exception:
            start_port = start_port + 1

    CLIENTHOST = sys.argv[1]
    PORT = int(sys.argv[2])

    # basic client socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.sendall('HELO')
    time.sleep(.1)
    sock.sendall(str(start_port))
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)

    while (reply_code != 'SUCC') and (reply_code != 'FAIL'):
        user_input = raw_input('>' + description)
        sock.sendall(user_input)
        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)

    if reply_code == 'FAIL':
        print description
        sock.close()
        exit(0)
    else:
        USERNAME = sock.recv(RECV_SIZE)
        mailbox = sock.recv(RECV_SIZE)
        description = description + '\n' + mailbox
        sock.close()

    logged_in = True
    listener = threading.Thread(target=listener_thread, args=(client_sock,))
    listener.daemon = True
    listener.start()

    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    while logged_in:

        sys.stdout.write(description + '\n>')
        sys.stdout.flush()
        user_input = raw_input()
        input_array = user_input.split()

        if input_array[0] == 'broadcast':
            user_input = user_input + ' ' + USERNAME
        elif input_array[0] == 'message':
            user_input = user_input + ' ' + USERNAME

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall('CMND')
        time.sleep(.1)
        sock.sendall(user_input)
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