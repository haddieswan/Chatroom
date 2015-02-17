import socket


# give host and port information
HOST = 'localhost'
PORT = int(raw_input('PORT NUMBER: '))

# basic client socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
while 1:
    userInput = raw_input('>')
    s.send(userInput)
    data = s.recv(1024)
    print 'Received', data
s.close()
