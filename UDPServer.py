import socket
import json


# clasa nod contine un dictionar care va reprezenta tabela de rutare
# initial un nod stie informatii doar despre el si distanta le el, care este 0
# ulterior putem adauga vecinii si distanta la ei
# trimitem mesaje la vecini si daca primim mesaj inapoi updatam tabela noastra de rutare
# cu numele vecinului si distanta pana la ei
#                       y  ( 192.168.0.1)
#                    /     \
#                   /       \
#               1  /         \   2
#                 /           \
#   (192.168.0.0)x  --------   z  (192.168.0.2)
#                        5
class Node:
    def __init__(self):
        self.origin = "192.168.0.0"
        self.indx = 0
        self.neighbors = {self.indx: ["192.168.0.0", 0]}

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
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((udp_ip, udp_port))

# creez tabela pt nodul meu
nod2 = Node()
# adaug nodurile vecine si costul pana la ele
nod2.addNeighbors('192.168.0.1', 1)
nod2.addNeighbors('192.168.0.2', 5)
print("Tabela mea este:    ")
print('Destinatie         cost')
for key in nod2.neighbors:
    print(str(nod2.neighbors[key][0]) + "         " + str(nod2.neighbors[key][1]))

while 1:
    data, address = socket.recvfrom(1024)
    # convertim din standard json inapoi in dictionar pt a putea sa prelucram valorile
    t = json.loads(data.decode())
    nghTable = t["a"]  # contine tabela de rutare primita

    print("Am primit de la client tabela:    ")
    print('Destinatie         cost')
    for key in nghTable:
        print(str(nghTable[key][0]) + "         " + str(nghTable[key][1]))

    # implementare algoritm bellman ford pentru a determina daca tabela primita ne ofera o ruta mai buna catre noduri
    for indx in nod2.neighbors.keys():  # parcurg tabela mea de rutare
        if nghTable[str(indx)][0] != nod2.origin and indx - 1 > 0:
            # inlocuiesc in tabela in momentul in care gasesc o ruta de cost mai mic
            if nod2.neighbors[indx][1] > nod2.neighbors[indx - 1][1] + nghTable[str(indx)][1]:
                nod2.neighbors[indx][1] = nod2.neighbors[indx - 1][1] + nghTable[str(indx)][1]

    print("Trimit mesaj la client tabela mea de rutare.")
    packet2 = Packet()
    packet2.addValues(nod2.neighbors)
    d2 = json.dumps({"a": packet2.vector})
    # trimit tabela de rutare la nodul vecin
    socket.sendto(d2.encode(), address)
