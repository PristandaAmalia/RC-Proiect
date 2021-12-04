import random
import socket

#UDP Server :

#1.Create a UDP socket.
#2.Bind the socket to the server address.
#3.Wait until the datagram packet arrives from the client.
#4.Process the datagram packet and send a reply to the client.
#5.Go back to Step 3.


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 5432))

while True:
    rand = random.randint(0, 10)
    message, address = server_socket.recvfrom(1024)
    message = message.upper()
    if rand >= 4:
        server_socket.sendto(message, address)