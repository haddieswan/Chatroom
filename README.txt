Multithreaded Chatroom
Programming Assignment 1
CSEE 4119 - Computer Networks

The following is a chatroom built using python. It is multithreaded using Python's threading module. It is currently designed for chat on a single computer (simulating client / server model as well as P2P by using different ports), but should be able to be scaled with a few tweaks. You can run the program as such:

python Server.py <port_number>

python Client.py <server_ip_address> <server_port_number>

You can run many instances of the client for a single server instance. This is partly because the server does not utilize persistent TCP connections, but rather uses a heartbeat model.

The extra credit option of guaranteed delivery was done and all required function have been implemented and are working as expected.
