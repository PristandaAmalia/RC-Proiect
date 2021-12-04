import random
import socket

#UDP Server :

#1.Create a UDP socket.
#2.Bind the socket to the server address.
#3.Wait until the datagram packet arrives from the client.
#4.Process the datagram packet and send a reply to the client.
#5.Go back to Step 3.


class Server:
    def __init__(self, ipAddress, port):
        print('creating server...')
        self.ipAddress=ipAddress
        self.port=port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ipAddress,self.port))

    def handle_request(self,data,address):
        print('handling message...')
        data=data.decode()
        print('mesajul ajuns la server este: '+data)
        data=data.upper()
        self.sock.sendto(data.encode(), address)

    def wait_for_client(self):
        print('waiting for client...')
        data, address = self.sock.recvfrom(1024)
        self.handle_request(data,address)

    def close_server(self):
        print('closing server...')
        self.sock.close()

def main():
    udp_server=Server('127.0.0.1',5555)
    udp_server.wait_for_client()


if __name__=='__main__':
    main()
