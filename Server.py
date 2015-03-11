import Queue
import socket
import signal
import os
import threading
import time
import sys
from multiprocessing import Lock


RECV_SIZE = 1024
TIMEOUT = 45
LOCKOUT = 30
user_list = []
lock = Lock()
user_lock = 0
PORT = 0
HOST = ''

# class for users on the client side
class User:
    'Common class for all users in this chat program'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.active = False
        self.logged_in = False
        self.port = 0
        self.ip = ''
        self.mailbox = []
        self.blocked_me = {}
        self.private_peer = ''
        self.locked_out = False

    def __str__(self):
        return self.username

# find in user by username
def find_user(username):
    global user_list
    for u in user_list:
        if u.username == username:
            return u
    return None

# multithread safe addition of user
def thread_add_user(user):
    global lock
    lock.acquire()
    try:
        user.logged_in = True
    finally:
        lock.release()

# multithread safe removal of user
def thread_remove_user(user):
    global lock
    lock.acquire()
    try:
        user.logged_in = False
        user.port = 0
    finally:
        lock.release()

# multithread safe heartbeat function
def thread_update_live_user(user):
    global lock
    lock.acquire()
    try:
        user.active = True
    finally:
        lock.release()

# multithread safe update of user port
def thread_add_user_port_ip(user, port, ip):
    global lock
    lock.acquire()
    try:
        user.port = int(port)
        user.ip = ip
    finally:
        lock.release()

def thread_add_blocking_user(user, blocking_user):
    global lock
    lock.acquire()
    try:
        user.blocked_me[blocking_user] = 1
    finally:
        lock.release()

def thread_remove_blocking_user(user, blocking_user):
    global lock
    lock.acquire()
    try:
        del user.blocked_me[blocking_user]
    finally:
        lock.release()

def thread_add_private_peer(user, peer):
    global lock
    lock.acquire()
    try:
        user.private_peer = peer
    finally:
        lock.release()

def thread_lock_out_user(user):
    global lock
    lock.acquire()
    try:
        user.locked_out = True
    finally:
        lock.release()

def thread_unlock_out_user(user):
    global lock
    lock.acquire()
    try:
        user.locked_out = False
    finally:
        lock.release()

def thread_add_to_mailbox(user, message):
    global lock
    lock.acquire()
    try:
        user.mailbox.append(message)
    finally:
        lock.release()

def thread_clear_mailbox(user):
    global lock
    lock.acquire()
    try:
        user.mailbox = []
    finally:
        lock.release()

# multithread safe check of all the live users
def thread_check_pulse():
    global lock
    global user_list
    lock.acquire()
    try:
        for user in user_list:
            if user.logged_in == True and user.active == False:
                user.logged_in = False
                broadcast_message(user.username + ' logged out', user.username)
            user.active = False
    finally:
        lock.release()

    time.sleep(TIMEOUT)
    check = threading.Thread(target=thread_check_pulse)
    check.daemon = True
    check.start()
    
    return(0)

# return string with pretty printed online users
def get_online_users():
    global user_list
    username_list = []

    for user in user_list:
        if user.logged_in == True:
            username_list.append(user.username)

    return '\n'.join(username_list)

def broadcast_message(message, sender):
    global user_list

    for user in user_list:
        if user.logged_in == True and user.username != sender:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((user.ip, user.port))
                delay_send(sock, 'BCST', message)
            except Exception:
                print 'client connection closed'
            sock.close()

def send_message(message, sender, receiver, code):

    rec_user = find_user(receiver)
    if rec_user == None or receiver == sender:
        ret_user = find_user(sender)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ret_user.ip, ret_user.port))
            delay_send(sock, code, receiver + ' is not a valid user.')
        except Exception:
            # guaranteed delivery, will at least go to mailbox
            thread_add_to_mailbox(ret_user, message)
        sock.close()
    elif rec_user.logged_in == True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((rec_user.ip, rec_user.port))
            delay_send(sock, code, message)
        except Exception:
            # guaranteed delivery, will at least go to mailbox
            thread_add_to_mailbox(rec_user, message)
        sock.close()
    else:
        thread_add_to_mailbox(rec_user, message)

def delay_send(connection, code, message):    
    try:
        connection.sendall(code)
        time.sleep(.1)
        connection.sendall(message)
    except Exception:
        print 'connection broken'

def check_port_free(port_number):
    global user_list
    for user in user_list:
        if user.port == port_number:
            return False
    return True

def lock_out_timeout(user):
    global LOCKOUT
    time.sleep(LOCKOUT)
    thread_unlock_out_user(user)
    return 0

# serve the connections
def serve_client(connection):

    global user_list

    greeting = connection.recv(RECV_SIZE)
    if greeting == 'PTCK':
        port_to_check = int(connection.recv(RECV_SIZE))
        port_free = check_port_free(port_to_check)
        if port_free:
            delay_send(connection, 'GDPT', '')
        else:
            delay_send(connection, 'BDPT', '')
    elif greeting == 'HELO':

        port_ip = connection.recv(RECV_SIZE).split()
        port = port_ip[0]
        ip = port_ip[1]
        delay_send(connection, 'USER', 'Username: ')
        username = connection.recv(RECV_SIZE)

        # check to see if it's a valid username
        user = find_user(username)
        if user == None:
            try:
                delay_send(connection, 'FAIL', 'User not found. Try again')
            except Exception:
                print 'client connection closed'
        elif user.locked_out == True:
            delay_send(connection, 'FAIL', 
                'Your account is still locked out\n')
        else:
            # otherwise, it passes the first tests
            verified = authenticate(connection, user, username)

            if verified:

                if user.logged_in == False:
                    thread_add_user(user)
                    thread_add_user_port_ip(user, port, ip)
                    delay_send(connection, 'SUCC', 
                        '>Welcome to simple chat server!')
                    time.sleep(.1)

                    # check mail
                    if not user.mailbox:
                        mail = '>No offline messages'
                    else:
                        mail = '\n'.join(user.mailbox)
                        thread_clear_mailbox(user)

                    delay_send(connection, username,
                        '>Offline Messages:\n' + mail)
                    broadcast_message(username + ' logged in', username)
                else:
                    delay_send(connection, 'FAIL', 
                        'Your account is already logged in\n')
    elif greeting == 'LIVE':

        username = connection.recv(RECV_SIZE)
        print 'LIVE: ' + username
        user = find_user(username)

        if user == None:
            print 'user broke off'
        elif user.logged_in == False:
            print 'user died, no heartbeat'
        else:
            thread_update_live_user(user)
            delay_send(connection, 'LIVE', 'Still living')
    elif greeting == 'CMND':

        user_input = connection.recv(RECV_SIZE)
        username = connection.recv(RECV_SIZE)
        user = find_user(username)
        input_array = user_input.split()

        if user == None:
            print 'user broke off'
        elif user_input == 'logout':

            thread_remove_user(user)
            delay_send(connection, 'LOGO', 'logout')
            broadcast_message(username + ' logged out', username)
        elif user_input == 'online':

            online_users = get_online_users()
            delay_send(connection, 'ONLN', online_users)
        elif input_array[0] == 'broadcast':

            delay_send(connection, 'BCST', '')
            input_array.remove(input_array[0])
            message = ' '.join(input_array)
            broadcast_message(username + ': ' + message, username)
        elif input_array[0] == 'message':

            delay_send(connection, 'MESG', '')
            receiver = input_array[1]
            input_array.remove(input_array[0])
            input_array.remove(input_array[0])

            try:
                user.blocked_me[receiver]
                send_message('You are blocked by ' + receiver, '', 
                    username, 'MESG')
            except Exception:
                message = ' '.join(input_array)
                send_message(username + ': ' + message, username, receiver, 
                    'MESG')
        elif input_array[0] == 'getaddress':

            contact = input_array[1]
            contact_user = find_user(contact)
            if(len(input_array) == 2 and username != contact
                and contact_user.logged_in):
                try:
                    user.blocked_me[contact]
                    delay_send(connection, 'NGET', 'Blocked by ' + contact)
                except Exception:
                    thread_add_private_peer(user, contact)
                    send_message(username + ' is requesting a private chat. ' + 
                        'To share your IP and port with them, reply saying ' +
                        '\'consent '+ username +'\'', username, contact, 'RQST')
            else:
                delay_send(connection, 'NGET', 'Invalid request')
        elif input_array[0] == 'consent':

            contact = input_array[1]
            if len(input_array) == 2 and username != contact:
                peer = find_user(contact)
                if username == peer.private_peer:
                    send_message(str(user.port) + ' ' + user.ip +  ' ' + 
                        username, username, contact, 'GETA')
                else:
                    send_message(contact + ' has not requested a P2P chat ' +
                        'with you. Use the getaddress command to start one',
                        contact, username, 'NGET')
        elif input_array[0] == 'block':

            to_block = input_array[1]
            if len(input_array) == 2 and username != to_block:
                thread_add_blocking_user(find_user(to_block), username)
                delay_send(connection, 'BLOK', '')
            else:
                delay_send(connection, 'NBLK', 'Unable to block user')
        elif input_array[0] == 'unblock':

            to_unblock = input_array[1]
            if len(input_array) == 2 and username != to_unblock:
                thread_remove_blocking_user(find_user(to_unblock), username)
                delay_send(connection, 'UBLK', '')
            else:
                delay_send(connection, 'NUBK', 'Unable to unblock user')
        else:
            delay_send(connection, 'RECV', 'server: ' + user_input)

    connection.close()
    print 'thread terminated'
    return(0)

# parent process which keeps accepting connections
def main_thread():
    
    global user_list
    global PORT
    global HOST

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
        user_list.append(User(line[0], line[1]))
        next_line = file_obj.readline()
    
    check = threading.Thread(target=thread_check_pulse)
    check.daemon = True
    check.start()

    while True:

        conn, addr = s.accept()

        print 'Connected by ', addr
        t = threading.Thread(target=serve_client, args=(conn,))
        t.start()

# authenticate the user
def authenticate(connection, user, username):
    global TIMEOUT

    count = 0
    verified = False
    correct_pass = user.password
    delay_send(connection, 'PASS', 'Password: ')
    
    while count < 3 and not verified:
        try:
            password = connection.recv(RECV_SIZE)
        except Exception:
            print 'connection with user broken'

        if password == correct_pass:
            verified = True
        elif count == 2:
            thread_lock_out_user(user)
            t = threading.Thread(target=lock_out_timeout, args=(user,))
            t.daemon = True
            t.start()

            delay_send(connection, 'FAIL', 'Due to multiple login failures, ' + 
                                   'your account has been blocked. Please ' +
                                   'try again after ' + str(TIMEOUT) + 
                                   ' seconds.')
        else:
            delay_send(connection, 'DENY', 'Invalid Password. ' + 
                                           'Please try again\n>Password: ')
        count = count + 1

    return verified

def ctrl_c_handler(signum, frame):
    exit(0)

def main():
    signal.signal(signal.SIGINT, ctrl_c_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    main_thread()

if __name__ == '__main__': 
    main()