import socket
import json
import struct
import sys

import netifaces

# clasa nod contine un dictionar care va reprezenta tabela de rutare
# initial un nod stie informatii doar despre el si distanta le el, care este 0
# ulterior putem adauga vecinii si distanta la ei
# trimitem mesaje si daca primim mesaj inapoi updatam tabela noastra de rutare
# cu numele si distanta pana la nod
#                       y  ( 192.168.0.1)
#                    /     \
#                   /       \
#               1  /         \   2
#                 /           \
#   (192.168.0.0)x  --------   z  (192.168.0.2)
#                        5

mcast_group = '224.1.1.1'
mcast_port = 5007
server_address = ('', 5007)


class Node:
    def __init__(self):
        self.origin = "192.168.0.0"
        self.indx = 0
        self.neighbors = {self.indx: ["192.168.0.0", 0]}

    # adaugam vecinii nodului curent in vector
    def addNeighbors(self, neighbor1, cost):
        self.indx += 1
        self.neighbors[self.indx] = [neighbor1, cost]

    def printTable(self):
        for neighbor in self.neighbors:
            print('Destinatie: ' + str(self.neighbors[neighbor][0] + '    cost: ' + str(self.neighbors[neighbor][1])))

    def update_table(self, newTable):
        # implementare algoritm bellman ford pentru a determina daca tabela primita ne ofera o ruta mai buna catre
        # noduri
        for indx in self.neighbors.keys():  # parcurg tabela mea de rutare
            if newTable[str(indx)][0] != nod2.origin and indx - 1 > 0:
                # inlocuiesc in tabela in momentul in care gasesc o ruta de cost mai mic
                if self.neighbors[indx][1] > self.neighbors[indx - 1][1] + newTable[str(indx)][1]:
                    self.neighbors[indx][1] = self.neighbors[indx - 1][1] + newTable[str(indx)][1]

# fiecare nod are tabelul de rutare ce contine destinatia, next-hop
# si distanta de la nodul nostru la destinatie
# prin pachete vom trimite vectorii de distanta
class Packet:
    def __init__(self):
        self.vector = {}  # dictionar ce contine nodul destinatie si costul pana la el

    def addValues(self, vector):
        self.vector = vector


def send(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    # trimitem datele mai departe
    sock.sendto(data, (mcast_group, mcast_port))


def recv():
    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind to the server address
    sock.bind(server_address)
    group = socket.inet_aton(mcast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    data, address = sock.recvfrom(1024)
    return data


if __name__ == '__main__':

    # creez tabela pt nodul meu
    nod2 = Node()
    # adaug nodurile vecine si costul pana la ele
    nod2.addNeighbors('192.168.0.1', 1)
    nod2.addNeighbors('192.168.0.2', 5)
    nod2.printTable()
    print("Trimit mesaj tabela mea de rutare.")

    if sys.argv[1] == "recv":
        d = recv()
        t = json.loads(d.decode())
        nghTable = t["a"]  # contine tabela de rutare primita
        print('Destinatie         cost')
        for key in nghTable:
            print(str(nghTable[key][0]) + "         " + str(nghTable[key][1]))
        nod2.update_table(nghTable)
        print('Tabela updatata este:')
        nod2.printTable()
        print("Trimit mesaj tabela mea de rutare.")
    else:
        packet2 = Packet()
        packet2.addValues(nod2.neighbors)
        d2 = json.dumps({"a": packet2.vector})

        # trimit tabela de rutare
        send(d2.encode())