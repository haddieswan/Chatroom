import Queue
import socket
import os
import threading


RECV_SIZE = 1024
online_users = []
lock = 0

# multithread safe addition of user
def add_user(username):
    global lock
    while lock:
        # spin, do nothing
        pass
    lock = 1
    online_users.append(username)
    lock = 0

# serve the connections
def serve_client(connection, dictionary):
    verified = authenticate(connection, dictionary)

    if verified:
        while True:
            
            data = connection.recv(RECV_SIZE)
            print data

            if data == 'online':
                data = ', '.join(online_users)

            if not data: break
            connection.sendall(data)
        print 'connection closed'
        connection.close()

    else:
        connection.sendall('Due to multiple login failures, your account has ' +
                           'been blocked. Please try again after sometime.')
        connection.close()
    return

# parent process which keeps accepting connections
def main_thread():
    HOST = ''
    PORT = int(raw_input('PORT NUMBER: '))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_pass_dict = {}
    ppid = os.getpid()

    s.bind((HOST, PORT))
    s.listen(1)

    file_obj = open('credentials.txt', 'r')
    next_line = file_obj.readline()
    while next_line != '':
        line = str.split(next_line, '\n')
        line = str.split(line[0], ' ')
        user_pass_dict[line[0]] = line[1]
        next_line = file_obj.readline()
    
    while True:

        conn, addr = s.accept()

        print 'Connected by ', addr
        t = threading.Thread(target=serve_client, args=(conn, user_pass_dict))
        t.start()

# authenticate the user
def authenticate(connection, dictionary):
    
    count = 0
    verified = False
    connection.sendall('Username: ')
    username = connection.recv(RECV_SIZE)
    correct_pass = dictionary[username]
    connection.sendall('Password: ')
    
    while count < 2 and not verified:
        
        password = connection.recv(RECV_SIZE)

        if password == correct_pass:
            verified = True
            connection.sendall('Welcome to simple chat server!\n>')
        else:
            connection.sendall('Invalid Password. ' + 
                               'Please try again\n>Password: ')
        count = count + 1

    if verified and (online_users.count(username) == 0):
        add_user(username)
    return verified

if __name__ == '__main__':
    main_thread()