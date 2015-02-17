import socket
import signal


SIG_INT = 2

def ctrl_c_handler(signum, frame):
    exit()

signal.signal(SIG_INT, ctrl_c_handler)

# give host and port information
HOST = 'localhost'
PORT = int(raw_input('PORT NUMBER: '))

# basic client socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST, PORT))
while 1:
    data = s.recv(1024)
    userInput = raw_input('>' + data)
    s.send(userInput)
    
s.close()
