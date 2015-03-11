from multiprocessing import Lock
import socket
import signal
import time
import threading
import random
import sys
import os

RECV_SIZE = 1024
HOST = ''
CLIENTHOST = ''
CLIENTPORT = 0
HEARTBEAT = 30
PORT = 0
USERNAME = ''
lock = Lock()
p2p_lock = Lock()
p2p_port = 0
p2p_ip = ''
p2p_user = ''

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
    global p2p_lock
    global p2p_port
    global p2p_ip
    global p2p_user

    reply_code = connection.recv(RECV_SIZE)
    message = connection.recv(RECV_SIZE)
    lock.acquire()
    try:
        sys.stdout.write(message + '\n>')
        sys.stdout.flush()
    finally:
        lock.release()

    if reply_code == 'LOGO':
        connection.close()
        os._exit(1)

    if reply_code == 'GETA':
        p2p_lock.acquire()
        try:
            private_info = message.split()
            p2p_port = int(private_info[0])
            p2p_ip = private_info[1]
            p2p_user = private_info[2]
        finally:
            p2p_lock.release()

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
        if user_input == '':
            user_input = '\n'
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

    global lock
    global p2p_port
    global p2p_ip
    global p2p_user
    logged_in = True

    while logged_in:


        lock.acquire()
        try:
            sys.stdout.write(description + '\n>')
            sys.stdout.flush()
        finally:
            lock.release()
            
        description = ''
        user_input = raw_input()
        if user_input == '':
            user_input = '\n'
        input_array = user_input.split()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p2p = False
        if len(input_array) >= 2:
            if input_array[0] == 'private' and input_array[1] == p2p_user:
                p2p = True
        if p2p:
            sock.connect((p2p_ip, p2p_port))
            message = user_input[(len('private ') + len(p2p_user) + 1):]
            delay_send(sock, 'P2PC', USERNAME + ': ' + message)
        else:
            sock.connect((HOST, PORT))
            delay_send(sock, 'CMND', user_input)
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
