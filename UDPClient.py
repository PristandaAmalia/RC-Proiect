import time
import socket

#In UDP, the client does not form a connection with the server like in TCP and instead just sends a datagram.
# Similarly, the server need not accept a connection and just waits for datagrams to arrive.
# Datagrams upon arrival contain the address of the sender which the server uses to send data to the correct client.

#UDP Client :

#1.Create a UDP socket.
#2.Send a message to the server.
#3.Wait until response from the server is received.
#4.Process reply and go back to step 2, if necessary.
#5.Close socket descriptor and exit.

for pings in range(10):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #A socket timeout stops the connection after a specified amount of time.
    #A socket timeout is dedicated to monitor the continuous incoming data flow.
    #If the data flow is interrupted for the specified timeout the connection is regarded as stalled/broken
    client_socket.settimeout(1.0)
    message = b'Buna'
    addr = ("127.0.0.1", 5432)

    start = time.time()
    client_socket.sendto(message, addr)
    try:
        data, server = client_socket.recvfrom(1024)
        end = time.time()
        elapsed = end - start
        print(f'{data} {pings} {elapsed}')
    except socket.timeout:
        print('REQUEST TIMED OUT')