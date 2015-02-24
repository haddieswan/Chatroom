import Queue
import socket
import signal
import os
import threading
import time
import sys
from multiprocessing import Lock


RECV_SIZE = 1024
TIMEOUT = 30
user_list = []
lock = Lock()
user_lock = 0

# class for users on the client side
class User:
    'Common class for all users in this chat program'

    def __init__(self, username, password, active, loggedin):
        self.username = username
        self.password = password
        self.active = active
        self.loggedin = loggedin

    def __str__(self):
        return self.username

# find in user by username
def find_user(username):
    for u in user_list:
        if u.username == username:
            return u
    return None

# multithread safe addition of user
def thread_add_user(user):
    global lock
    lock.acquire()
    try:
        user.loggedin = True
    finally:
        lock.release()

# multithread safe removal of user
def thread_remove_user(user):
    global lock
    lock.acquire()
    try:
        user.loggedin = False
    finally:
        lock.release()

# multithread safe heartbeat function
def update_live_user(user):
    global lock
    lock.acquire()
    try:
        user.active = True
    finally:
        lock.release()

# serve the connections
def serve_client(connection):
    print 'fresh thread launched'

    global user_list
    greeting = connection.recv(RECV_SIZE)
    print greeting
    # logging in for the first time
    if greeting == 'HELO':

        connection.sendall('USER')
        # is this necessary???
        time.sleep(.1)
        connection.sendall('Username: ')
        username = connection.recv(RECV_SIZE)

        # check to see if it's a valid username
        user = find_user(username)
        if user == None:
            try:
                connection.sendall('FAIL')
                time.sleep(.1)
                connection.sendall('User not found. Try again')
            except Exception:
                print 'client connection closed'
        else:
            # otherwise, it passes the first test
            verified = authenticate(connection, user, username)

            if verified:

                if user.loggedin == False:
                    thread_add_user(user)
                    connection.sendall('SUCC')
                    time.sleep(.1)
                    connection.sendall('Welcome to simple chat server!')
                    time.sleep(.1)
                    connection.sendall(username)
                else:
                    connection.sendall('FAIL')
                    time.sleep(.1)
                    connection.sendall('Your account is already logged in\n')
    elif greeting == 'LIVE':
        username = connection.recv(RECV_SIZE)
        print 'heartbeat received from ' + username
        user = find_user(username)

        if user == None:
            print 'user broke off'
        elif user.loggedin == False:
            connection.sendall('DEAD')
            time.sleep(.1)
            connection.sendall('Logged out')
        else:
            user # = find correct user
            update_live_user(user)
            connection.sendall('LIVE')
            time.sleep(.1)
            connection.sendall('Still living')
    elif greeting == 'CMND':
        userInput = connection.recv(RECV_SIZE)
        username = connection.recv(RECV_SIZE)
        user = find_user(username)
        # print 'command received: ' + userInput
        if user == None:
            print 'user broke off'
        elif userInput == 'logout':
            thread_remove_user(user)
            connection.sendall('LOGO')
            time.sleep(.1)
            connection.sendall('logout')
        else:
            connection.sendall('RECV')
            time.sleep(.1)
            connection.sendall('received' + userInput)

    connection.close()
    print 'thread terminated'

# parent process which keeps accepting connections
def main_thread():
    
    global user_list

    if len(sys.argv) < 2:
        print 'usage: python Server.py <PORT NUMBER>'
        exit(1)

    HOST = ''
    PORT = int(sys.argv[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((HOST, PORT))
    s.listen(1)

    file_obj = open('credentials.txt', 'r')
    next_line = file_obj.readline()
    while next_line != '':
        line = str.split(next_line, '\n')
        line = str.split(line[0], ' ')
        user_list.append(User(line[0], line[1], False, False))
        next_line = file_obj.readline()
    
    while True:

        conn, addr = s.accept()

        print 'Connected by ', addr
        t = threading.Thread(target=serve_client, args=(conn,))
        t.start()

# authenticate the user
def authenticate(connection, user, username):

    count = 0
    verified = False
    correct_pass = user.password
    connection.sendall('PASS')
    time.sleep(.1)
    connection.sendall('Password: ')
    
    while count < 3 and not verified:
        
        password = connection.recv(RECV_SIZE)

        if password == correct_pass:
            verified = True
        elif count == 2:
            connection.sendall('FAIL')
            time.sleep(.1)
            connection.sendall('Due to multiple login failures, your account ' +
                               'has been blocked. Please try again after ' +
                               'sometime.')
        else:
            connection.sendall('DENY')
            time.sleep(.1)
            connection.sendall('Invalid Password. ' + 
                               'Please try again\n>Password: ')
        count = count + 1

    return verified

def ctrl_c_handler(signum, frame):
    exit(0)

def main():
    signal.signal(signal.SIGINT, ctrl_c_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    main_thread()

if __name__ == '__main__': main()