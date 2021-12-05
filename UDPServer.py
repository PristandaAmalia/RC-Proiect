import random
import socket


# UDP Server :

# 1.Create a UDP socket.
# 2.Bind the socket to the server address.
# 3.Wait until the datagram packet arrives from the client.
# 4.Process the datagram packet and send a reply to the client.
# 5.Go back to Step 3.

# clasa nod contine un dictionar care va reprezenta tabela de rutare
# initial un nod stie informatii doar despre el si distanta le el, care este 0
# ulterior putem adauga vecinii si distanta la ei
# trimitem mesaje la vecini si daca primim mesaj inapoi updatam tabela noastra de rutare
# cu numele vecinului si distanta pana la ei
#              y
#           /     \
#          /       \
#      1  /         \   2
#        /           \
#   x      --------   z
#              5
class Node:
    def __init__(self):
        self.neighbors = {'X': 0}

    # adaugam vecinii nodului curent in vector
    def addNeighbors(self, neighbor1, cost):
        self.neighbors[neighbor1] = cost


# fiecare nod are tabelul de rutare ce contine destinatia, next-hop
# si distanta de la nodul nostru la destinatie
# prin pachete vom trimite vectorii de distanta
class Packet:
    def __init__(self):
        self.vector = {}  # dictionar ce contine nodul destinatie si costul pana la el

    def addValues(self, vector):
        self.vector = vector


class Server:
    def __init__(self, ipAddress, port):
        print('creating server...')
        self.ipAddress = ipAddress
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ipAddress, self.port))

    def handle_request(self, data, address):
        print('handling message...')
        data = data.decode()
        print('mesajul ajuns la server este: ' + data)
        data = data.upper()
        self.sock.sendto(data.encode(), address)

    def wait_for_client(self):
        print('waiting for client...')
        data, address = self.sock.recvfrom(1024)
        self.handle_request(data, address)

    def close_server(self):
        print('closing server...')
        self.sock.close()


def main():
    udp_server = Server('127.0.0.1', 5555)
    udp_server.wait_for_client()


if __name__ == '__main__':
    main()
