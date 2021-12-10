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
        self.origin = "192.168.0.1"
        self.neighbors = {"192.168.0.1": 0}

    # adaugam vecinii nodului curent in vector
    def addNeighbors(self, neighbor1, cost):
        self.neighbors[neighbor1] = cost

    def printTable(self):
        print('Tabela mea este')
        for neighbor in self.neighbors:
            print('Destinatie: ' + str(neighbor + '    cost: ' + str(self.neighbors[neighbor])))

    # addr este adresa de la care primim tabela de rutare
    def update_table(self, newTable, addr):
        # implementare algoritm bellman ford pentru a determina daca tabela primita ne ofera o ruta mai buna catre
        # noduri
        adresses = []
        # lista cu toate adresele continute in tabela de rutara a mea
        for address in self.neighbors.keys():
            adresses.append(address)

        # verific daca in tabela primita este o adresa pe care nu o am, daca da o adaug
        for i in newTable.keys():
            if i not in adresses:  # adun la costul pana la nodul intermediar costul de la nodul intemediar pana la dest
                self.neighbors[i] = self.neighbors[addr] + newTable[i]

        for i in self.neighbors.keys():  # parcurg adresele
            # alg bellman-ford: daca valoarea prin nod intermediar(nodul al carui tabela de rutare il avem acum) este
            # mai buna decat cea din tabela noastra  o inlocuim
            if self.neighbors[i] > self.neighbors[addr] + newTable[i] and i != self.origin:
                self.neighbors[i] = self.neighbors[addr] + newTable[i]


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
    return data, address


if __name__ == '__main__':

    # creez tabela pt nodul meu
    nod2 = Node()
    # adaug nodurile vecine si costul pana la ele
    nod2.addNeighbors('192.168.0.0', 19)
    nod2.addNeighbors('192.168.0.2', 19)
    nod2.addNeighbors('192.168.0.3', 19)
    nod2.printTable()

    if sys.argv[1] == "recv":
        d, addr = recv()
        t = json.loads(d.decode())
        nghTable = t["a"]  # contine tabela de rutare primita
        print('Destinatie         cost')
        for key in nghTable:
            print(key + "         " + str(nghTable[key]))
        nod2.update_table(nghTable, '192.168.0.1')
        print('Tabela updatata este:')
        nod2.printTable()

    else:
        packet2 = Packet()
        packet2.addValues(nod2.neighbors)
        d2 = json.dumps({"a": packet2.vector})
        print("Trimit mesaj tabela mea de rutare.")
        # trimit tabela de rutare
        send(d2.encode())
