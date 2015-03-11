James Lin
jl3782
Multithreaded Chatroom
Programming Assignment 1
CSEE 4119 - Computer Networks



--- Running the Program / Sample Run ---

The following is a chatroom built using Python. The current configuration assumes you have a username-password file called 'credentials.txt' in which each line has <username> <password>. With this set up, you can run the program as such:

python Server.py <port_number>

# run this second step for as many clients as you want
python Client.py <server_ip_address> <server_port_number>

A Makefile is not necessary since the program was written in Python.

--
For example (good run and successful run):
--
# on computer A
python Server.py 8000

# on computer B
python Client.py 128.12.25.31 8000
>Username: columbia
>Password: 116bway
>Welcome to simple chat server!
>Offline Messages:
>No offline messages
>

--
For example (good run and unsuccessful login):
--
# on computer A
python Server.py 8000

# on computer B
python Client.py 128.12.25.31 8000
>Username: google
>Password: hasglassses
>Invalid Password. Please try again
>Password: hasgaases
>Invalid Password. Please try again
>Password: hasgas
Due to multiple login failures, your account has been blocked. Please try again after 60 seconds.



--- Programming Design and Structure / Source Code ---

My program is designed in two primary modules, Client.py and Server.py. The Server contains a single class called User, which is an object containing all the useful fields that individual users need. Because all of this is multithreaded, it was necessary to create multithread safe functions for writing/updating the users since they are located in global scope (as to avoid clobbering or race conditions). These functions make up much of Server.py. Beyond this, the Server primarily consists of a single "manager" thread which is continually spawning new threads to serve incoming connections. A series of if-statements deliver each connection to their correct piece of logic.

Clients mostly contain code to handshake with the Server (establish a connection) and then bring user commands to the Server. Multithreading is still required on the clients' side because of the heartbeat mechanism and needing to listen for incoming connections. Further details on both the Server.py and Client.py source code can be found within the comments. Notably, clients also act as 'servers' in P2P and host connections coming in from the server. Similarly, the server actually connects to the client-hosted IP and port when communicating with it/them.

My overall network protocol was one of CODE followed by DESCRIPTION. This CODE allowed for the two parties to communicate with one another and figure out what actions were needed. The DESCRIPTION on the other hand was intended for the human to actually see, for the program to actually print to console. I did my best to follow best Python programming practice and design, naming variables and organizing functions in as Pythonic of a way as possible.



--- Additional Features / Sample Test Cases ---

Bonus Features Implemented: P2P Privacy and Consent, Guaranteed Message Delivery

Both of these bonus features were relatively easy to implement, especially guaranteed message delivery. They allow peers to have greater control (via blacklisting and consent) over P2P contact and guarantee that messages sent through the server will somehow get delivered.

--
MESSAGE
--
|               A               |             B            |              C           |
>message
Invalid Command: message
>message not_a_user
not_a_user is not a valid user.
>message B
                                >A:
>message B hello!               
                                >A: hello!
>message C yooooo!
                                                            >A: yooooo!


--
BROADCAST / PRESENCE / BLOCK / UNBLOCK / ONLINE / GETADDRESS / MESSAGE
--
|               A               |             B             |              C           |
>broadcast
                                >A:                         >A:
>broadcast psa                  >A: psa                     >A: psa
>block B
User B has been blocked
                                >message A hello?
                                You are blocked by A
                                >getaddress A
                                Blocked by A
                                >broadcast check 1 2 3
                                                            >B: check 1 2 3
                                >online
                                C
                                                            >online
                                                            A
                                                            B
>broadcast to everyone!         
                                >A: to everyone!            >A: to everyone!
>unblock B
User B is unblocked
                                >broadcast check 1 2 3
>B: check 1 2 3                                             >B: check 1 2 3
>block B
User B has been blocked
>logout
$                                                           >A logged out

--
GETADDRESS / CONSENT / PRIVATE
--
|               A               |             B             |              C           |
>getaddress
Invalid Command: getaddress
>getaddress A
Invalid request
>getaddress B
                                >B is requesting a private
                                chat. To share your IP and 
                                port with them, reply saying
                                'consent A'
                                >consent A
>28403 160.39.204.24 B
>private B p2p message
                                >A: p2p message
                                >private A p2p message
                                Invalid Command: private A
                                p2p message
                                >^C
>private B another p2p
B is no longer at this address.
You can send them an offline 
message through the server.







