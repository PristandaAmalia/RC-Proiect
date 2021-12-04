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


    #A socket timeout stops the connection after a specified amount of time.
    #A socket timeout is dedicated to monitor the continuous incoming data flow.
    #If the data flow is interrupted for the specified timeout the connection is regarded as stalled/broken
class Client:
    def __init__(self,data):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data=data

    def send_message(self,address):
        print('sending message to server...')
        self.sock.sendto(self.data.encode(), address)


        data, server = self.sock.recvfrom(1024)
        data = data.decode()
        print('mesajul trimis de ' + server[0] + ' la client este: '+data)


    def receive_message(self):
        pass

def main():
    udp_client=Client('Clientul spune "Buna!"')
    udp_client.send_message(('127.0.0.1',5555))

if __name__=='__main__':
    main()
