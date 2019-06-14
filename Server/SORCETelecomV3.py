import socket
import sys
import DualBME280s
import datetime
import time
import threading
from UFC6000 import FrequencyCounter
from koheron_control import *
from arduino_lock_cmd_dual_output import *
from arduno_lock_cmd import *





## Initialization
frequency_counter = FrequencyCounter(address="/dev/FREQCOUNT")
frequency_counter.set_sample_time(1)

kc1 = KoheronController("/dev/Koheron1")
kc2 = KoheronController("/dev/Koheron2")

ardCurLock1 = ArduinoCurrentLocker("/dev/Arduino1")
ardCurLock2 = ArduinoCurrentLocker("/dev/Arduino2")


DataLog = open("DataLog.txt","a+")
DataLog.close()



def freqCounter():
    return (frequency_counter.get_frequency_and_range())
    
def associate(Data,conn):
    message = ""
    if Data[0:4] == "Ping":
       message = "pong"
       
       
    if len(Data)> 4:
        if Data[0:4] == "Temp":
            if Data[4] == "?":
                temp = DualBME280s.temp()
                message = "Temperature: " + str(temp[0]) + ", " + str(temp[1]) 
       

    if Data[0:3] == "Alt":
        if Data[3] == "?":
            message = "Altitude is of Z"
    if Data[0:5] == "Humid":
        if Data[5] == "?":
            humid = DualBME280s.humidity()
            message = "Humidity: " + str(humid[0]) + ", " + str(humid[1])
    if Data[0:8] == "Pressure":
        if Data[8] == "?":
            pressure = DualBME280s.pressure()
            message = "Pressure: " + str(pressure[0]) + ", " + str(pressure[1]) 

    if Data[0:3] == "Loc":
        if Data[3] == "?":
            message = "X: XPLACEHOLDER" + " " + "Y: YPLACEHOLDER" + " " + "Z: ZPLACEGOLDER"
    if Data[0:2] == "kc":
        if Data[2] == "1":
            if Data[3:10] == ".write(":
                command = Data[10:len(Data)-1]
                kc1.write(command)
            elif Data[3:8] == ".ask(":
                command = Data[8:len(Data)-1]
                message = "Response: " +str(kc1.ask(command))
            elif Data[3:9] == ".close":
                kc1.close()
            elif Data[3:13] == ".set_temp(":
                temp = float(Data[12:len(Data)-1])
                kc1.set_temp(temp)
                message = "Temperature has been set to: " + str(temp)
            elif Data[3:17] == ".read_set_temp":
                message = "Read Temperature: " + str(kc1.read_set_temp())
            elif Data[3:13] == ".read_temp":
                message = str(kc1.read_temp())
            elif Data[3:16] == ".set_current(":
                curr = float(Data[16:len (Data)-1])
                kc1.set_current(curr)
                message = "Current has been set to: " + str(curr)
            elif Data[3:12] == ".laser_on":
                kc1.laser_on()
                message = "Laser has been turned On"
            elif Data[3:13] == ".laser_off":
                kc1.laser_off()
                message = "Laser has been turned off"
            elif Data[3:16] == ".read_current":
                message = str(kc1.read_current())
            elif Data[3:21] == ".increase_current(":
                adj = float(Data[21:len(Data)-1])
                kc1.increase_current(adj)
                message = "Current has been increased to: " + str(adj)
            elif Data[3:21] == ".decrease_current(":
                adj = float(Data[21:len(Data)-1])
                kc1.decrease_current(adj)
                message = "Current has been decreased to: " + str(adj)
            elif Data[3:13] == ".get_temp(":
                res = float(Data[13:len(Data)-1])
                message = " Temp is of " + str(kc1.get_temp(res))
            elif Data[3:19] == ".get_resistance(":
                temp = float(Data[19:len(Data)-1])
                message = "The resistance is of: "str(kc1.get_resistance(temp))
        if Data[2] == "2":
            if Data[3:10] == ".write(":
                command = Data[10:len(Data)-1]
                kc2.write(command)
            elif Data[3:8] == ".ask(":
                command = Data[8:len(Data)-1]
                message = str(kc2.ask(command))
            elif Data[3:9] == ".close":
                kc2.close()
            elif Data[3:13] == ".set_temp(":
                temp = float(Data[12:len(Data)-1])
                kc2.set_temp(temp)
            elif Data[3:17] == ".read_set_temp":
                message = str(kc2.read_set_temp())
            elif Data[3:13] == ".read_temp":
                message = str(kc2.read_temp())
            elif Data[3:16] == ".set_current(":
                curr = float(Data[16:len (Data)-1])
                kc2.set_current(curr)
            elif Data[3:12] == ".laser_on":
                kc2.laser_on()
            elif Data[3:13] == ".laser_off":
                kc2.laser_off()
            elif Data[3:16] == ".read_current":
                message = str(kc1.read_current())
            elif Data[3:21] == ".increase_current(":
                adj = float(Data[21:len(Data)-1])
                kc2.increase_current(adj)
            elif Data[3:21] == ".decrease_current(":
                adj = float(Data[21:len(Data)-1])
                kc2.decrease_current(adj)
            elif Data[3:13] == ".get_temp(":
                res = float(Data[13:len(Data)-1])
                message = str(kc2.get_temp(res))
            elif Data[3:19] == ".get_resistance(":
                temp = float(Data[19:len(Data)-1])
                message = str(kc2.get_resistance(temp))                
                
    if message == "":
        message = "Invalid Input"

    
    return message


def run():
    while True:
        ### Data Connection
        DHOST = ""
        DPORT = 1329 ###Data Port
        d = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                 
        try:
            d.bind((DHOST,DPORT))
        except:
            d.bind((DHOST,DPORT+1))
            
        try:
            # Opening the Data Connection
            d.listen(10)
            dConn, dAddr = d.accept()
            print("Connection at",dAddr)
        except:
            print("Data not Connected")
                
        time.sleep(1)
        while True:
            DataLog = open("DataLog.txt","a+")
            try:
                temp = DualBME280s.temp()
                #freq = freqCounter()
                
                
                message = str(datetime.datetime.now())+"\t" + str(temp[0]) + "\t" + str(temp[1]) + "\t\n" #+ str(freq[1]) + "\n"
                DataLog.write(message)
                dConn.sendto(message.encode(),dAddr)
            except:
                print("Disconnected at", str(datetime.datetime.now()))
                dConn.close()
                DataLog.close()
                break
              
                
            DataLog.close()
            
            
        
        print("over")
    return True
    
        

def main():

    ## Loop over everything
    while True:
        # Initializing the connections

        ### CMD connection
        HOST = ""
        PORT = 1313###Data Port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((HOST,PORT))
        except:
            s.bind((HOST,PORT+1))
    
        
        Started = False
        
        
        #Trying to connect the connection
        try:
            # Opening the CMD connection
            s.listen(10)
            conn, addr = s.accept()

            print("Connection at",addr)
        except:
            print("CMD not Connected")
        time.sleep(0.5)        
        
        ### Loop to start the connection
        while True:
            data = conn.recv(1024)
            if data.decode() == "Start":


                ### Open the command/warning Log
                log = open("logs.txt","a+")
                log.write("---------------------------------------------------------------------------------------------------------------\n")
                log.write("Time: " + str(datetime.datetime.now()) + " Connected: " + str(addr) + "\n")        
              
                ### Data Thread Starting
                try:
                    threadData = threading.Thread(target=run)
                    threadData.start()

                except:
                    log.write("Time: " + str(datetime.datetime.now()) + " WARNING: THREAD ALREADY INITIATED\n")

                ### Validation of Connection
                message = "Connected!"
                conn.sendall(message.encode())
                logLine = "Time: " + str(datetime.datetime.now()) + " Input: " + data.decode() + " Output: " + message + "\n"
                log.write(logLine)
                
                ### Breaking out of loop
                Started = True
                break

            ### Incase the client tries to send a command before initializing the connection.
            else:
                message = "ERROR: Process has not started"
                conn.sendall(message.encode())
                
        
        while True:
            try:
                data = conn.recv(1024)
            except:
                log.write("Time: " + str(datetime.datetime.now()) + " Disconnected: " + str(addr) + "\n")
                print("Disonnection at",addr)

                log.close()

                
                Started = False
                conn.close()

                break
            
            
            if not data:
                break
                
            if data.decode() == "Terminate":
                log.write("Time: " + str(datetime.datetime.now()) + " Disconnected: " + str(addr) + "\n")
                print("Disonnection at",addr)

                log.close()                    
                
                Started = False
                conn.close()

                s.shutdown(socket.SHUT_RDWR)

                break
            
            else:
                if Started == True:   
                    message = associate(data.decode(),conn)
                    
                else:
                    message = "ERROR: Process has not started"
                
                conn.sendall(message.encode())
                logLine = "Time: " + str(datetime.datetime.now()) + " Input: " + data.decode() + " Output: " + message + "\n"
                log.write(logLine)
            
        conn.close()


        
   
    
main()
