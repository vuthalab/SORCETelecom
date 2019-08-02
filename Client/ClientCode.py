import socket
import time
import threading
import os
#os.chdir("/home/labuser/Desktop")



## function definitions
def dataGetter():
    
    dhost = 'localhost'#'192.168.0.148'
    dport = 1329


    d = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    try:
        d.connect((dhost,dport))
    except:
        dport = dport+1
        d.connect((dhost,dport))
        
    while True:

        connected = True
        try:
            log = open("NewDataAugust2nd.txt","a+")
        except:
            print("Already Opened")
        try:
            val = (d.recv(1024)).decode()
            if val != "":
                log.write(val + "\n")
        except:
            print("Exception")
            connected = False
            while not connected:
                print("in")
                d.close()
                d = socket.socket()
                d.connect((dhost,dport))
                connected = True
                # print("Out")
        try:
            #print("closed")
            log.close()
        except:
            print("Already Closed")
    return True


## main routines
host = 'localhost'#'192.168.0.148'
port = 1313


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((host,port))
except:
    s.connect((host,port+1))




## main loop
while True:

    s.sendall(("Start").encode())

    time.sleep(2)
    
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