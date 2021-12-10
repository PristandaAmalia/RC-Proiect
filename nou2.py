import socket
import threading
import struct
import time
import json
from multiprocessing import Lock
adreseIp = ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5']

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5004

ttl = 16

mutex=threading.Lock()
#ar trebui sa am o metoda de sincronizare a datelor=>mutex?
class TabelaRutare:
    dict = {}


    def __init__(self):
        # tabela de rutare va fi de forma Destinatie:NextHop:metrica

        # prima oara in tabela am doar host-ul

        self.dict.update({socket.gethostname(): ['', 0]})

    def encodeTabela(self):
        return json.dumps(self.dict).encode("utf-8")

    def updateRuta(self, dest, nextHop, metrica):
        mutex.acquire()
        self.dict[dest] = [nextHop, metrica]
        mutex.release()


tabelaRutare = TabelaRutare()


class Network:


    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.configure()
        # using daemon thread the main thread can completely forget about this task and this task will either complete or killed when main thread exits.
        threading.Thread(target=self.sendMessage, daemon=True).start()

    def configure(self):



        # luat de pe stackoverflow

        # multicast sender that broadcasts to a multicast group

        # ttl controls how many networks will receive the packet
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        # multicast receiver that reads from a multicast group
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


        # on this port, listen ONLY to MCAST_GRP
        self.sock.bind((MCAST_GRP, MCAST_PORT))

        # sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
        #sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MCAST_GRP) + socket.inet_aton(ip))

        # the receiver listens to all interfaces using INADDR_ANY

        # am luat o de pe programcreek.com
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.receiveMessage()

    # din 30 in 30 de secunde trimit tabela de rutare catre alt calculator
    def sendMessage(self):

        self.sock.sendto(tabelaRutare.encodeTabela(), (MCAST_GRP, MCAST_PORT))
        time.sleep(30)

    def handle_request(self, newTable, clientAdress):

        newTable = newTable.decode("utf-8")

        # daca exista deja cheia in tabela mea de rutare atunci vad daca exista o ruta mai buna
        # daca nu atunci o adaug
        for y in newTable:
            if y in tabelaRutare.dict.keys():
                if tabelaRutare.dict[y][1] > newTable[y][1] + tabelaRutare.dict[clientAdress][1]:
                    tabelaRutare.updateRuta(y, clientAdress, newTable[y][1] + tabelaRutare.dict[clientAdress][1])

            else:
                mutex.acquire()
                tabelaRutare.dict.update({y: [newTable[y][0], newTable[y][1] + 1]})
                mutex.release()

    def receiveMessage(self):
        while True:

            data,client_address=self.sock.recvfrom(1024)

            c_thread = threading.Thread(target = self.handle_request, args = (data,client_address))
            c_thread.daemon=True
            c_thread.start()

network = Network()

