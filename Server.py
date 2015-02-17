import socket
import os


# parent process which keeps accepting connections
def parent():
    HOST = ''
    PORT = int(raw_input('PORT NUMBER: '))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    
    while True:
        conn, addr = s.accept()
        print 'Connected by ', addr
        newpid = os.fork()
        if newpid == 0:
            child(conn)

# children which serve the connections
def child(connection):
    while True:
        data = connection.recv(1024)
        print data
        if not data: break
        connection.sendall(data)
    connection.close()
    os._exit(0)

parent()