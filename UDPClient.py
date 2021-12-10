import random
import socket
import struct
import sys
import json


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
        self.origin = "192.168.0.1"
        self.indx = 0
        self.neighbors = {self.indx: ["192.168.0.1", 0]}

    # adaugam vecinii nodului curent in vector
    def addNeighbors(self, neighbor1, cost):
        self.indx += 1
        self.neighbors[self.indx] = [neighbor1, cost]


# fiecare nod are tabelul de rutare ce contine destinatia, next-hop
# si distanta de la nodul nostru la destinatie
# prin pachete vom trimite vectorii de distanta
class Packet:
    def __init__(self):
        self.vector = {}  # dictionar ce contine nodul destinatie si costul pana la el

    def addValues(self, vector):
        self.vector = vector


udp_ip = "127.0.0.1"
udp_port = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


nod = Node()
nod.addNeighbors('192.168.0.0', 1)
nod.addNeighbors('192.168.0.2', 2)
packet = Packet()
packet.addValues(nod.neighbors)
d = json.dumps({"a": packet.vector})

sock.sendto(d.encode(), (udp_ip, udp_port))

data, address = sock.recvfrom(1024)
t = json.loads(data.decode())
nghTable = t["a"]  # contine tabela de rutare primita

print("Am primit de la server tabela:    ")
print('Destinatie         cost')
for key in nghTable:
    print(str(nghTable[key][0]) + "         " + str(nghTable[key][1]))
