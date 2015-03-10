from multiprocessing import Lock
import socket
import signal
import time
import threading
import random
import sys

RECV_SIZE = 1024
HOST = ''
CLIENTHOST = ''
CLIENTPORT = 0
HEARTBEAT = 30
PORT = 0
USERNAME = ''
lock = Lock()

def ctrl_c_handler(signum, frame):
    exit(0)

def delay_send(connection, code, message):    
    try:
        connection.sendall(code)
        time.sleep(.1)
        connection.sendall(message)
    except Exception:
        print 'connection broken'

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
    delay_send(sock, 'LIVE', USERNAME)
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)
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

    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    CLIENTHOST = socket.gethostbyname(socket.gethostname())

    CLIENTPORT = random.randint(1023, 65535)
    while True:

        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        delay_send(sock, 'PTCK', str(CLIENTPORT))

        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)

        if reply_code == 'GDPT':
            try:
                client_sock.bind((CLIENTHOST, CLIENTPORT))
                client_sock.listen(1)
                break
            except Exception:
                CLIENTPORT = CLIENTPORT + 1
        else:
            CLIENTPORT = start_port + 1

    # basic client socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    delay_send(sock, 'HELO', str(CLIENTPORT) + ' ' + CLIENTHOST)
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

    listener = threading.Thread(target=listener_thread, args=(client_sock,))
    listener.daemon = True
    listener.start()

    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    logged_in = True
    p2p_port = 0
    p2p_user = ''

    while logged_in:

        global lock
        lock.acquire()
        try:
            sys.stdout.write(description + '\n>')
            sys.stdout.flush()
        finally:
            lock.release()
            
        description = ''
        user_input = raw_input()
        input_array = user_input.split()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if input_array[0] == 'private' and input_array[1] == p2p_user:
            sock.connect((HOST, p2p_port))
            input_array.reverse()
            input_array.pop()
            input_array.pop()
            input_array.reverse()
            sock.sendall(USERNAME + ': ' + ' '.join(input_array))
        else:
            sock.connect((HOST, PORT))
            delay_send(sock, 'CMND', user_input)
            time.sleep(.1)
            sock.sendall(USERNAME)

            reply_code = sock.recv(RECV_SIZE)
            description = sock.recv(RECV_SIZE)

            if reply_code == 'LOGO':
                logged_in = False
            elif reply_code == 'GETA':
                private_info = description.split()
                p2p_port = int(private_info[0])
                p2p_user = private_info[1]
        sock.close()

    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, ctrl_c_handler)
    main()
