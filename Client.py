'''
James Lin
jl3782
Client.py -- CSEE 4119 Programming Assignment 1
'''

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

# ^C graceful termination
def ctrl_c_handler(signum, frame):
    exit(0)

# delay send to fix a python socket issue
def delay_send(connection, code, message):    
    try:
        connection.sendall(code)
        time.sleep(.1)
        connection.sendall(message)
    except Exception:
        print 'connection broken'

# serve client of the client (incoming connections)
def serve_client(connection):
    global lock
    global p2p_lock
    global p2p_port
    global p2p_ip
    global p2p_user

    reply_code = connection.recv(RECV_SIZE)
    message = connection.recv(RECV_SIZE)

    # make sure text arrives in order by locking
    lock.acquire()
    try:
        sys.stdout.write(message + '\n>')
        sys.stdout.flush()
    finally:
        lock.release()

    # exit if someone else logs you off
    if reply_code == 'LOGO':
        connection.close()
        os._exit(1)

    # safely update the p2p information if received
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

# manager thread for clients of client
def listener_thread(client_sock):

    while True:
        conn, addr = client_sock.accept()
        server = threading.Thread(target=serve_client, args=(conn,))
        server.start()

# heartbeat thread that periodically pings server
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

    # run as daemon so that everything terminates at close
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

    # pick a random port to minimize collisions
    CLIENTPORT = random.randint(1023, 65535)
    while True:

        # communicate client port and ip information to server
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        delay_send(sock, 'PTCK', str(CLIENTPORT))

        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)

        # make sure that the port is good, otherwise linear probing
        if reply_code == 'GDPT':
            try:
                client_sock.bind((CLIENTHOST, CLIENTPORT))
                client_sock.listen(1)
                break
            except Exception:
                CLIENTPORT = CLIENTPORT + 1
        else:
            CLIENTPORT = start_port + 1


    # initial contact to get user prompt
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    delay_send(sock, 'HELO', ' ')
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)
    sock.close()

    # wait for user to type in username
    username = raw_input('>' + description)
    if username == '':
        username = 'non_user'

    # follow-up to get username input
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    delay_send(sock, 'USER', username + ' ' + str(CLIENTPORT) + ' ' +
        CLIENTHOST)
    reply_code = sock.recv(RECV_SIZE)
    description = sock.recv(RECV_SIZE)
    sock.close()

    # 3 password tries
    try_num = 1
    while (reply_code != 'SUCC') and (reply_code != 'FAIL'):
        user_input = raw_input('>' + description)
        if user_input == '':
            user_input = 'non_pass'

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        delay_send(sock, 'AUTH', username + ' ' + user_input + 
            ' ' + str(try_num))
        
        try_num = try_num + 1
        reply_code = sock.recv(RECV_SIZE)
        description = sock.recv(RECV_SIZE)
        
        if reply_code == 'SUCC':
            USERNAME = sock.recv(RECV_SIZE)
            mailbox = sock.recv(RECV_SIZE)
            description = description + '\n' + mailbox            
        
        sock.close()

    if reply_code == 'FAIL':
        print description
        exit(0)

    # launch the client listening thread
    listener = threading.Thread(target=listener_thread, args=(client_sock,))
    listener.daemon = True
    listener.start()

    # launch the heartbeat thread
    t = threading.Thread(target=heartbeat)
    t.daemon = True
    t.start()

    global lock
    global p2p_port
    global p2p_ip
    global p2p_user
    logged_in = True

    # user command and input
    while logged_in:

        # make sure things print in order
        lock.acquire()
        try:
            sys.stdout.write(description + '\n>')
            sys.stdout.flush()
        finally:
            lock.release()
            
        # grab user input
        description = ''
        user_input = raw_input()
        if user_input == '':
            user_input = '\n'
        input_array = user_input.split()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p2p = False
        # test for p2p case
        if len(input_array) >= 2:
            if input_array[0] == 'private' and input_array[1] == p2p_user:
                p2p = True
        if p2p:
            # make sure p2p is not offline
            try:
                sock.connect((p2p_ip, p2p_port))
                message = user_input[(len('private ') + len(p2p_user) + 1):]
                delay_send(sock, 'P2PC', USERNAME + ': ' + message)
            except Exception:
                print (p2p_user + ' is no longer at this address. You can ' +
                    'send them an offline message through the server.')
        else:
            # otherwise send command
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
