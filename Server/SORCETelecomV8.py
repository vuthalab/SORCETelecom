import socket
import sys
#import Imports.DualBME280s as DualBME280s
import datetime
import time
import threading
#from Imports.UFC6000 import FrequencyCounter
#from Imports.koheron_control import *
#from Imports.arduino_lock_cmd_dual_output import *
#from Imports.arduino_lock_cmd import *


### Initialization of Koherons and Arduinos
#time.sleep(0.5)
#frequency_counter = FrequencyCounter(address="/dev/FREQCOUNT")
#frequency_counter.set_sample_time(1)

#kc1 = KoheronController("/dev/Koheron1")
#kc2 = KoheronController("/dev/Koheron2")

#ard1 = ArduinoCurrentLocker("/dev/Arduino1")
#ard2 = ArduinoCurrentLocker("/dev/Arduino2")


DataLog = open("DataLog.txt","a+")
DataLog.close()


### Initializing the frequency counter
def freqCounter():
    return (frequency_counter.get_frequency_and_range())
    
### Function for associating a query to a given function and creating + sending the message
def associate(Data,conn):
    message = ""
    if Data[0:4] == "Ping":
       message = "pong"
       
       
    elif Data[0:5] == "Temp?":
       temp = DualBME280s.temp()
       message = "Temperature: " + str(temp[0]) + ", " + str(temp[1]) 

    elif Data[0:4] == "Alt?":
        message = "Altitude is of Z"

    elif Data[0:6] == "Humid?":
       humid = DualBME280s.humidity()
       message = "Humidity: " + str(humid[0]) + ", " + str(humid[1])
    
    elif Data[0:9] == "Pressure?":
        pressure = DualBME280s.pressure()
        message = "Pressure: " + str(pressure[0]) + ", " + str(pressure[1]) 

    elif Data[0:4] == "Loc?":
        message = "X: XPLACEHOLDER" + " " + "Y: YPLACEHOLDER" + " " + "Z: ZPLACEGOLDER"
            
    elif Data[0:10] == "Frequency?":
        freq = freqCounter() 
        message = "Frequency is of: " + str(freq[1]) + " MHz"
            
    elif Data[0:3] == "ard":
        if Data[3] == "1":
            if Data[4:21] == ".default_params()":
                ard1.default_params()
                message = "Default Params have been set"
            elif Data[4:10] == ".idn()":
                message = ard1.idn()
            elif Data[4:23] == ".load_from_eeprom()":
                ard1.load_from_eeprom()
                message = "Loaded from EEPROM"
            elif Data[4:] == ".save_to_eeprom()":
                ard1.save_to_eeprom()
                message = "Saved to EEPROM"
            elif Data[4:] == ".get_params()":
                message = str(ard1.get_params())
            elif Data[4:] == ".set_params()":
                message = ard1.set_params()
            elif Data[4:20] == ".set_scan_state(":
                state = Data[20:len(Data)-1]
                ard1.set_scan_state(state)
                message = "State has been set"
            elif Data[4:] == ".get_data()":
                message = str(ard1.get_data())
            elif Data[4:] == ".get_sampling_rate()":
                message = ard1.get_sampling_rate()
            elif Data[4:] == ".close()":
                ard1.close()
                message = "Closed"
            elif Data[4:] == ".print_params()":
                message = ard1.print_params()
            elif Data[4:14] == ".scan_amp(":
                amp = Data[14:len(Data)-1]
                ard1.scan_amp(float(amp))
                message = "Scan Amp has been set"
            elif Data[4:] == ".lock()":
                ard1.lock()
                message = "Locked"
            elif Data[4:] == ".unlock()":
                ard1.unlock()
                message = "Unlocked"
            elif Data[4:12] == ".gain_p(":
                pgain = Data[12:len(Data)-1]
                ard1.gain_p(float(pgain))
                message = "P gain set"
            elif Data[4:12] == ".gain_i(":
                igain = Data[12:len(Data)-1]
                ard1.gain_i(float(igain))
                message = "I gain set"
            elif Data[4:13] == ".gain_i2(":
                i2gain = Data[13:len(Data)-1]
                ard1.gain_i2(float(i2gain))
                message = "i2 Gain set"
            elif Data[4:19] == ".output_offset(":
                offset = Data[19:len(Data)-1]
                ard1.output_offset(float(offset))
                message = "Offset has been set"
            elif Data[4:] == ".increase_offset()":
                ard1.increase_offset()
                message = "Offset sucessfully Increased"
            elif Data[4:] == ".decrease_offset()":
                ard1.dectrase_offset()
                message = "Offset sucessfully Decreased"
            elif Data[4:10] == ".fwhm(":
                fwhm = Data[10:len(Data)-1]
                ard1.fwhm(float(fwhm))
                message = "FWHM set"
            elif Data[4:16] ==  ".n_averages(":
                n = Data[16:len(Data)-1]
                ard1.n_averages(int(n))
                message = "N Averages set"
            elif Data[4:14] == ".low_pass(":
                lp = Data[14:len(Data)-1]
                message = ard1.low_pass(int(lp))
                
        elif Data[3] == "2":
            if Data[4:21] == ".default_params()":
                ard2.default_params()
                message = "Default Params have been set"
            elif Data[4:10] == ".idn()":
                message = ard2.idn()
            elif Data[4:23] == ".load_from_eeprom()":
                ard2.load_from_eeprom()
                message = "Loaded from EEPROM"
            elif Data[4:] == ".save_to_eeprom()":
                ard2.save_to_eeprom()
                message = "Saved to EEPROM"
            elif Data[4:] == ".get_params()":
                message = str(ard2.get_params())
            elif Data[4:] == ".set_params()":
                message = ard2.set_params()
            elif Data[4:20] == ".set_scan_state(":
                state = Data[20:len(Data)-1]
                ard2.set_scan_state(state)
                message = "State has been set"
            elif Data[4:] == ".get_data()":
                message = str(ard2.get_data())
            elif Data[4:] == ".get_sampling_rate()":
                message = ard2.get_sampling_rate()
            elif Data[4:] == ".close()":
                ard2.close()
                message = "Closed"
            elif Data[4:] == ".print_params()":
                message = ard2.print_params()
            elif Data[4:14] == ".scan_amp(":
                amp = Data[14:len(Data)-1]
                ard2.scan_amp(float(amp))
                message = "Scan Amp has been set"
            elif Data[4:] == ".lock()":
                ard2.lock()
                message = "Locked"
            elif Data[4:] == ".unlock()":
                ard2.unlock()
                message = "Unlocked"
            elif Data[4:12] == ".gain_p(":
                pgain = Data[12:len(Data)-1]
                ard2.gain_p(float(pgain))
                message = "P gain set"
            elif Data[4:12] == ".gain_i(":
                igain = Data[12:len(Data)-1]
                ard2.gain_i(float(igain))
                message = "I gain set"
            elif Data[4:13] == ".gain_i2(":
                i2gain = Data[13:len(Data)-1]
                ard2.gain_i2(float(i2gain))
                message = "i2 Gain set"
            elif Data[4:19] == ".output_offset(":
                offset = Data[19:len(Data)-1]
                ard2.output_offset(float(offset))
                message = "Offset has been set"
            elif Data[4:] == ".increase_offset()":
                ard2.increase_offset()
                message = "Offset sucessfully Increased"
            elif Data[4:] == ".decrease_offset()":
                ard2.dectrase_offset()
                message = "Offset sucessfully Decreased"
            elif Data[4:10] == ".fwhm(":
                fwhm = Data[10:len(Data)-1]
                ard2.fwhm(float(fwhm))
                message = "FWHM set"
            elif Data[4:16] ==  ".n_averages(":
                n = Data[16:len(Data)-1]
                ard2.n_averages(int(n))
                message = "N Averages set"
            elif Data[4:14] == ".low_pass(":
                lp = Data[14:len(Data)-1]
                message = ard2.low_pass(int(lp))
            
                
    elif Data[0:2] == "kc":
        if Data[2] == "1":
            if Data[3:10] == ".write(":
                command = Data[10:len(Data)-1]
                kc1.write(command)
                message = "Command has been written"
            elif Data[3:8] == ".ask(":
                command = Data[8:len(Data)-1]
                message = "Response: " +str(kc1.ask(command))
            elif Data[3:9] == ".close":
                kc1.close()
                message = "Closed"
            elif Data[3:13] == ".set_temp(":
                temp = float(Data[13:len(Data)-1])
                kc1.set_temp(temp)
                message = "Temperature has been set to: " + str(temp)
            elif Data[3:17] == ".read_set_temp":
                message = "Set Temperature: " + str(kc1.read_set_temp())
            elif Data[3:13] == ".read_temp":
                message = "Temperature is:" + str(kc1.read_temp())
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
                message = "Current is of: " + str(kc1.read_current())
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
                message = " Temperature is of " + str(kc1.get_temp(res))
            elif Data[3:19] == ".get_resistance(":
                temp = float(Data[19:len(Data)-1])
                message = "The resistance is of: "+ str(kc1.get_resistance(temp))
            elif Data[3:] == ".stream_data()":
                temp = get_temp(float(kc1.ask('rtact')))
                curr = float(kc1.ask('ilaser'))
                if(float(kc1.ask('lason'))==1):
                    onoff = 'On'
                else:
                    onoff = 'Off'
                message = "Temperature: " + str(temp) + " C   Laser: " + onoff + "   Current: " + str(curr) + " mA"
        elif Data[2] == "2":
            if Data[3:10] == ".write(":
                command = Data[10:len(Data)-1]
                kc2.write(command)
                message = "Command has been written"
            elif Data[3:8] == ".ask(":
                command = Data[8:len(Data)-1]
                message = "Response: " +str(kc2.ask(command))
            elif Data[3:9] == ".close":
                kc2.close()
                message = "Closed"
            elif Data[3:13] == ".set_temp(":
                temp = float(Data[12:len(Data)-1])
                kc2.set_temp(temp)
                message = "Temperature has been set to: " + str(temp)
            elif Data[3:17] == ".read_set_temp":
                message = "Set Temperature: " + str(kc2.read_set_temp())
            elif Data[3:13] == ".read_temp":
                message = "Temperature is:" + str(kc2.read_temp())
            elif Data[3:16] == ".set_current(":
                curr = float(Data[16:len (Data)-1])
                kc2.set_current(curr)
                message = "Current has been set to: " + str(curr)
            elif Data[3:12] == ".laser_on":
                kc2.laser_on()
                message = "Laser has been turned On"
            elif Data[3:13] == ".laser_off":
                kc2.laser_off()
                message = "Laser has been turned off"
            elif Data[3:16] == ".read_current":
                message = "Current is of: " + str(kc2.read_current())
            elif Data[3:21] == ".increase_current(":
                adj = float(Data[21:len(Data)-1])
                kc2.increase_current(adj)
                message = "Current has been increased to: " + str(adj)
            elif Data[3:21] == ".decrease_current(":
                adj = float(Data[21:len(Data)-1])
                kc2.decrease_current(adj)
                message = "Current has been decreased to: " + str(adj)
            elif Data[3:13] == ".get_temp(":
                res = float(Data[13:len(Data)-1])
                message = " Temperature is of " + str(kc2.get_temp(res))
            elif Data[3:19] == ".get_resistance(":
                temp = float(Data[19:len(Data)-1])
                message = "The resistance is of: "+ str(kc2.get_resistance(temp))
            elif Data[3:] == ".stream_data()":
                temp = get_temp(float(kc2.ask('rtact')))
                curr = float(kc2.ask('ilaser'))
                if(float(kc2.ask('lason'))==1):
                    onoff = 'On'
                else:
                    onoff = 'Off'
                message = "Temperature: " + str(temp) + " C   Laser: " + onoff + "   Current: " + str(curr) + " mA"

    if message == "":
        message = "Invalid Input"

    return message

### Code ran on the 3rd thread, to log any variables or error messages from the arduinos.
def getArduinoUpdates():
    #Give the arduinos a second to connect properly
    time.sleep(1)
    #Permanant loop for receiving the data from the arduinos
    while True: 
        #Writes all of the data to a different file.
        try:
            ArduinoLog = open("arduinoLog.txt","a+")
            update1 = ard1.ser.readline().decode("utf-8").replace("\n","")
            update2 = ard2.ser.readline().decode("utf-8").replace("\n","")
            message = str(datetime.datetime.now()) + "\t" + str(update1[0:len(update1)-1])+ "\t" + str(update2[0:len(update2)-1]) + "\n"
            ArduinoLog.write(message)
            #print("Arduino1's update " + update1[0:len(update1)-1])
            #print("Arduino2's update " + update2[0:len(update2)-1])
            ArduinoLog.close()
        except:
            print("Err")
            try:
                ArduinoLog.close()
            except:
                print("Already closed")
            return True
        

### Code that sends the stream of data constantly
def run():
    while True:
        ### Data Connection
        DHOST = ""
        DPORT = 1329 ###Data Port
        d = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        d.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ##Tries to create the data connection to 1329, if it fails to 1330
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
                
        #Give the connection a second
        time.sleep(1)

        ### Loop for the logged and sent data.
        ### Currently Logs: Temperature from both sensors, Frequency from the Frequency counter and the Local time.
        ### Needs to log time from RTC and Altitude of the Gondola (Waiting on CSA for that) 2019-08-02
            # Sent them an email
        while True:
            try:
                DataLog = open("DataLog.txt","a+")
                #temp = DualBME280s.temp()
                #freq = freqCounter()               
                message = str(datetime.datetime.now())+"\t\n" #+ str(temp[0]) + "\t" + str(temp[1]) + "\t" + str(freq[1]) + "\n"
                DataLog.write(message)
                dConn.sendto((message + "\r").encode(),dAddr)
                DataLog.close()
            except:
                print("Disconnected at", str(datetime.datetime.now()))
                print("Failed")
                dConn.close()
                DataLog.close()
                try:
                    d.shutdown(socket.SHUT_RDWR)
                except:
                    d.close()
                break
        
        print("over")
    return True
    
        
### Main thread, handles the sending and receiving of commands.
def main():
    print("Start")
    
    TimeOutTime = 15 *3600 #in seconds
    StartTime= time.time()

    ## Loop over everything
    while True:
        # Initializing the connections

        ### CMD connection
        HOST = ""
        PORT = 1313 ###Data Port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ##Tries to create the connection at the port 1313, and if it fails it will create it to 1314.
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
                    # Starts the data sending thread
                    threadData = threading.Thread(target=run)
                    threadData.start()
                    # Starts the Arduino Updates thread
                    threadUpdate = threading.Thread(target=getArduinoUpdates)
                    threadUpdate.start()

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
                
        ### Loop that handles communication to the client
        while True:
            # Code first checks if more time has elapsed than the alloted time (Maximum time alloted = TimeOutTime)
            if (time.time() - StartTime) >= TimeOutTime:
                kc1.laser_off()
                while float(kc1.ask('lason'))==1:
                    kc1.laser_off()
                while float(kc2.ask('lason'))==1:
                    kc2.laser_off()

            # Code tries to read the query of the Client
            try:
                data = conn.recv(1024)
            except:
                # If no query has been received, the code logs it as an error and closes the log and restarts the connection process
                log.write("Time: " + str(datetime.datetime.now()) + " No Response From: " + str(addr) + "\n")
                print("Time: " + str(datetime.datetime.now()) + " No Response From: " + str(addr))

                log.close()
                Started = False
                conn.close()

                break
            # If the Query is somehow invalid, (returns a false?) it resets the question
            if not data:
                break

            ### If the client wants to terminate, this clause is initiated.
            #   This clause essentially disconnects the user, closes the log and closes the socket properly
            if data.decode() == "Terminate":
                log.write("Time: " + str(datetime.datetime.now()) + " Disconnected: " + str(addr) + "\n")
                print("Time: " + str(datetime.datetime.now()) + " Disconnected: " + str(addr) + "\n")


                log.close()                      
                Started = False
                conn.close()
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except:
                    s.close()

                break

            ### If the client does not want to terminate, the server decodes the data and accomplishes the command.
            else:
                # Fist checks that the process is "started"
                if Started == True:   
                    message = associate(data.decode(),conn)
                    
                else:
                    message = "ERROR: Process has not started"
                # After a successful translation, it sends the client a message and saves a copy to log.
                conn.sendall(message.encode())
                logLine = "Time: " + str(datetime.datetime.now()) + " Input: " + data.decode() + " Output: " + message + "\n"
                log.write(logLine)


        # After running the main loop sucessfully and ending it, the connection is then closed.    
        conn.close()    
   
    
main()
