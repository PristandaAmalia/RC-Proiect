import socket
import struct
import threading
import time
from tkinter import *
import netifaces
from prettytable import PrettyTable

mcast_group = '224.0.0.9'
mcast_port = 520

ip_interfaces = []
netmask_interfaces = []


update_timer = 30
invalid_timer = 180 #specifies how long a routing entry can be in the routing table without being updated
holddown_timer = 180 #nu mai pot primi informatii despre o ruta care la mine in tabel este invalida
flush_timer = 240 #controls the time between the route is invalidated or marked as unreachable and removal of entry from the routing table.


INFdist=16

running = False


#https://pypi.org/project/netifaces/
#----------------------------
for interface in netifaces.interfaces():
    if interface != "lo" and interface != "enp0s3":
        #----------------------------
        #addresses of a particular interface by doing netifaces.ifaddresses(interface)
        addr = netifaces.ifaddresses(interface)
        #addr[netifaces.AF_INET] -> [{'broadcast': '10.15.255.255', 'netmask': '255.240.0.0', 'addr': '10.0.1.4'}]

        ip = addr[netifaces.AF_INET][0]['addr']

        ip_interfaces.append(ip)

        netmask = addr[netifaces.AF_INET][0]['netmask']
        netmask_interfaces.append(netmask)
#------------------------------
lock = threading.Lock()


class TabelRutare:
    #entries = [ [destinationIP,subnetMASK,nextHop,metrica] ]

    def __init__(self):
        self.entries = []
        self.invalidTimer = {}
        self.holddownTimer = {}
        self.flushTimer = {}

    def updateTabel(self, tabelNou, adresa):
        #am tabelul nou de la adresa
        global invalid_timer
        global flush_timer
        global holddown_timer

        lock.acquire()

        try:
            for entryNou in tabelNou.entries:
                gasit = False

                #caut destinatia din tabelul nou in tabelul meu

                # split horizon
                if entryNou[2] not in ip_interfaces:

                    for entryVechi in self.entries:

                        if entryNou[0] == entryVechi[0]:
                            # cand gasesc o destinatie din tabelul primit deja exista in tabelul meu am 4 optiuni:
                            # 1. destinatia a devenit invalida
                            # 2. destinatia invalida si-a revenit
                            # 3. destinatia nu este invalida si poate fi updatata
                            # 4. niciuna dintre situatiile de mai sus => doar updatez timerele
                            # 1 si 3 pot fi facute doar daca holdtime timer-ul pentru destinatia mea nu este activ
                            gasit = True
                            invalida = False
                            update = False
                            recovery = False

                            # daca adresa nu este una de la rutere, atunci informatiile sunt primite prin gateway

                            if self.holddownTimer[entryVechi[0]] == holddown_timer:

                                # 1.
                                if entryNou[3] == INFdist and entryVechi[2] == adresa:
                                    print(' am primit o ruta invalida')
                                    invalida = True
                                    # activez holdtime timerul pentru ruta mea
                                    self.invalidTimer[entryVechi[0]] = 0
                                    self.flushTimer[entryVechi[0]] = flush_timer - invalid_timer

                                # 3.
                                if entryVechi[3] > entryNou[3] + 1:
                                    print(' am primit o ruta mai buna')

                                    update = True

                                    entryVechi[3] = entryNou[3] + 1
                                    entryVechi[2] = adresa

                                    # resetez timerele
                                    self.invalidTimer[entryVechi[0]] = invalid_timer
                                    self.holddownTimer[entryVechi[0]] = holddown_timer
                                    self.flushTimer[entryVechi[0]] = flush_timer

                            else:
                                # 2.
                                if entryNou[3] != INFdist and entryVechi[2] == adresa:
                                    print(' ruta invalida si a revenit ')
                                    recovery = True
                                    entryVechi[3] = entryNou[3]+1

                                    self.invalidTimer[entryVechi[0]] = invalid_timer
                                    self.holddownTimer[entryVechi[0]] = holddown_timer
                                    self.flushTimer[entryVechi[0]] = flush_timer
                            # 4.
                            if recovery is False and update is False and invalida is False and entryVechi[2] == adresa:
                                self.invalidTimer[entryVechi[0]] = invalid_timer
                                self.flushTimer[entryVechi[0]] = flush_timer
                                self.holddownTimer[entryVechi[0]] = holddown_timer

                    if gasit is False:
                        # adaug destinatia in tabelul meu


                        if entryNou[3]+1 < INFdist:
                            print(' am primit o ruta noua')
                            self.entries.append([entryNou[0], entryNou[1], adresa, entryNou[3]+1])


                            #adaug o ruta noua => ii asociez timerele

                            self.invalidTimer[entryNou[0]] = invalid_timer
                            self.holddownTimer[entryNou[0]] = holddown_timer
                            self.flushTimer[entryNou[0]] = flush_timer

        finally:
            lock.release()




#https://stackoverflow.com/questions/5619685/conversion-from-ip-string-to-integer-and-backward-in-python
#--------------
def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))
#---------------

class RipV2:

    tabelRutare = TabelRutare()

    def __init__(self):
        global invalid_timer
        global holddown_timer
        global flush_timer

        k = 0
        for ip in ip_interfaces:
            entry = [ip, netmask_interfaces[k], '127.0.0.1', 0]

            self.tabelRutare.entries.append(entry)

            self.tabelRutare.invalidTimer[ip] = invalid_timer
            self.tabelRutare.flushTimer[ip] = flush_timer
            self.tabelRutare.holddownTimer[ip] = holddown_timer

            k = k+1

        self.mcast_sock_list = []

        #se creeaza socketurile multicast pentru fiecare interfata
        for ip in ip_interfaces:
            #https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
            #----------------------------------------
            #send
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20)


            #receive
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((mcast_group, mcast_port))

            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))

            mreq = socket.inet_aton(mcast_group) + socket.inet_aton(ip)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            #----------------------------------------
            self.mcast_sock_list.append(sock)


    def trimiteMesajRipV2(self):
        global running

        while running:

            print('*****trimit****')
            for sock in self.mcast_sock_list:
                sock.sendto(self.codeazaMesajRipV2(self.tabelRutare), (mcast_group, mcast_port))
            time.sleep(int(update_timer))

    def trimiteRutaInvalida(self, entry):

        tabelRutare = TabelRutare()
        tabelRutare.entries.append(entry)
        for sock in self.mcast_sock_list:
            sock.sendto(self.codeazaMesajRipV2(tabelRutare),(mcast_group,mcast_port))



    def primesteMesajRipV2(self):
        global running

        while running:
            data, address = self.mcast_sock_list[0].recvfrom(1024)
            print("S-a receptionat de la ", address[0])
            self.tabelRutare.updateTabel(self.decodeazaMesajRipV2(data), address[0])


    def codeazaMesajRipV2(self, tabelRutare):
        #antetul trebuie sa aiba 32 de biti

        #bitul de comanda = 1 (request message)
        command = 1#8 biti
        version = 2#8 biti
        unused = 0#16 biti
        mesaj = struct.pack('1b', command)+struct.pack('1b', version)+struct.pack('1h', unused)

        addressFamilyIdentifier = 4#8 biti
        routeTag = 0#8 biti

        #routeEntry este  address family identifier + route tag + intrarile din tabelul meu de rutare

        for entry in tabelRutare.entries:

            mesaj = mesaj + struct.pack('1h', addressFamilyIdentifier)+struct.pack('1h', routeTag)

            mesaj = mesaj + struct.pack('1I', ip2int(entry[0])) + struct.pack('1I', ip2int(entry[1])) + struct.pack('1I', ip2int(entry[2]))+struct.pack('1i', entry[3])

        return mesaj

    def decodeazaMesajRipV2(self, mesaj):


        command = struct.unpack('1b', mesaj[:1])[0]
        version = struct.unpack('1b', mesaj[1:2])[0]
        unused = struct.unpack('1h', mesaj[2:4])[0]

        mesaj = mesaj[4:]

        tabelRutareNou = TabelRutare()

        flag = True
        while flag:
            intrareTabel = []

            addressFamilyIdentifier = struct.unpack('1h', mesaj[0:2])[0]
            routeTag = struct.unpack('1h', mesaj[2:4])[0]

            mesaj = mesaj[4:]

            intrareTabel.append(str(int2ip(struct.unpack('1I', mesaj[0:4])[0])))
            mesaj = mesaj[4:]

            intrareTabel.append(str(int2ip(struct.unpack('1I', mesaj[0:4])[0])))
            mesaj = mesaj[4:]

            intrareTabel.append(str(int2ip(struct.unpack('1I', mesaj[0:4])[0])))
            mesaj = mesaj[4:]

            intrareTabel.append(struct.unpack('1i', mesaj[0:4])[0])
            mesaj = mesaj[4:]

            tabelRutareNou.entries.append(intrareTabel)
            if len(mesaj) == 0:
                flag = False
        return tabelRutareNou

    def checkTimers(self):
        global invalid_timer
        global holddown_timer
        global flush_timer
        global running

        while running:

            for entry in self.tabelRutare.entries:

                if entry[2] != '127.0.0.1':

                    destinatie = entry[0]

                    if self.tabelRutare.invalidTimer[destinatie] == 0:

                        # activez holddown timer

                        if self.tabelRutare.holddownTimer[destinatie] == holddown_timer:
                            self.tabelRutare.holddownTimer[destinatie] = self.tabelRutare.holddownTimer[destinatie] - 1

                            # marchez ruta ca fiind invalida si o trimit imediat vecinilor

                            print('Ruta ' + str(destinatie) + ' a devenit invalida')

                            entry[3] = INFdist
                            self.trimiteRutaInvalida(entry)

                        else:
                            self.tabelRutare.holddownTimer[destinatie] = self.tabelRutare.holddownTimer[destinatie] - 1

                    else:
                        self.tabelRutare.invalidTimer[destinatie] = self.tabelRutare.invalidTimer[destinatie] - 1

                    # sterg ruta din tabel daca flushTimer a expirat
                    if self.tabelRutare.flushTimer[destinatie] == 0:

                        print('Ruta ' + str(destinatie) + ' a fost stearsa')

                        self.tabelRutare.invalidTimer.pop(destinatie)
                        self.tabelRutare.flushTimer.pop(destinatie)
                        self.tabelRutare.holddownTimer.pop(destinatie)

                        self.tabelRutare.entries.remove(entry)

                    else:
                        self.tabelRutare.flushTimer[destinatie] = self.tabelRutare.flushTimer[destinatie]-1

            time.sleep(1)


def setToBox():

    tabel = PrettyTable()
    tabel.field_names=["Destinatia", "Subnet Mask", "Next Hop", "Metrica"]

    #sir = "Destinatia      Subnet Mask       Next Hop      Metrica\n"

    for entry in ripv2.tabelRutare.entries:
        #sir += str(entry[0]) + "      " + str(entry[1]) + "      " + str(entry[2]) + "      " + str(entry[3]) + "\n"

        tabel.add_row(entry)
        #print(sir)
    label.config(text="")
    label.config(text=tabel)
    label.pack()

def startRip():
    global running

    running = True
    threading.Thread(target=ripv2.trimiteMesajRipV2).start()
    threading.Thread(target=ripv2.primesteMesajRipV2).start()
    threading.Thread(target=ripv2.checkTimers).start()

def stopRip():
    global running

    running = False


def getInput():
    global update_timer

    inp = textBox.get(1.0, END)
    print(inp)
    update_timer = int(inp)


def getTimers():
    global invalid_timer
    global flush_timer
    global holddown_timer

    inp2 = textBox2.get(1.0, END)
    print(inp2)
    timers = inp2.split(',')
    if len(timers) != 0:
        invalid_timer = int(timers[0])
        flush_timer = int(timers[1])
        holddown_timer = int(timers[2])
        print(invalid_timer)
        print(flush_timer)
        print(holddown_timer)


if __name__ == '__main__':
    root = Tk()
    root.title("Ripv2")
    root.geometry("500x600")



    button1 = Button(root, text="Start", command=startRip)
    button1.pack()

    ripv2 = RipV2()

    label = Label(root, text="")
    button = Button(root, text="Print", command=setToBox)
    button.pack()

    label1 = Label(root, text="Update timer")
    label1.pack()
    textBox = Text(root, height=1, width=5)
    textBox.pack()
    button2 = Button(root, height=1, width=10, text="Commit", command=getInput)
    button2.pack()

    label2 = Label(root, text="Invalid timer, flush timer, holddown timer")
    label2.pack()
    textBox2 = Text(root, height=1, width=5)
    textBox2.pack()
    button3 = Button(root, height=1, width=10, text="Commit", command=getTimers)
    button3.pack()

    button4 = Button(root, text="Stop", command=stopRip)
    button4.pack()

    mainloop()
