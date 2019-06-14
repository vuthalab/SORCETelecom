import socket
import time
import threading
import os
os.chdir("/home/labuser/Desktop")



## function definitions
def dataGetter():
    global d
    while True:
        connected = True
        try:
            log = open("data.txt","a+")
        except:
            print("Already Opened")
        try:
            val = (d.recv(1024)).decode()
            log.write(val + "\n")
        except:
            # print("Exception")
            connected = False
            while not connected:
                if dGet == False: break
                # print("in")
                d.close()
                d = socket.socket()
                d.connect((dhost,dport))
                connected = True
                # print("Out")
        try:
            log.close()
        except:
            print("Already Closed")
    return True


## main routines
host = '172.20.3.181'
port = 1313

dhost = '172.20.3.181'
dport = 1329


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((host,port))
except:
    s.connect((host,port+1))




## main loop
while True:

    s.sendall(("Start").encode())

    time.sleep(2)
    d = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        d.connect((dhost,dport))
    except:
        d.connect((dhost,dport+1))
    print("ok")
    dGet = True
    threadData = threading.Thread(target=dataGetter)
    threadData.start()
    data = (s.recv(1024)).decode()

    print("Received Data:", data)
    while True:
        print("----------------------------------------")
        message = input("Message?\n")
        if message == "Stop":
            break
        s.sendall(message.encode())

        if message == "Terminate":
            print("Connection Terminated")
            s.close()
            dGet = False
            break

        if message == "Pause":
            dGet= False
            print("alright")
            time.sleep(0.5)
            s.sendall(message.encode())


        else:
            data = (s.recv(1024)).decode()
            print("Received Data:", data)
    break
