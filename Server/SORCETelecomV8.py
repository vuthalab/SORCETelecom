import socket
import sys
import datetime
import time
import threading
import struct 


###Trying to import functions from different sensors and apparatuses

# Importing the Temperature, Humidity adn Pressure Sensors
try:
    import Imports.DualBME280s as DualBME280s
except:
    print("DualBME280s cannot be imported")



# Importing the Frequency Counter
try:
    from Imports.UFC6000 import FrequencyCounter
except:
    print("UFC6000 could not be imported")   

# Importing the Koheron Controllers    
try:
    from Imports.koheron_control import *
except:
    print("Koheron could not be imported")

# Importing the Arduino's
try:
    from Imports.arduino_lock_cmd_dual_output import *
except:
    print("Could not import Arduino Lock CMD Dual Output")
try:   
   from Imports.arduino_lock_cmd import *
except:
    print("Could not import Arduino Lock CMD")


### Block for Initializing sensors and apparatuses
time.sleep(0.5)

# Trying to initialize the Frequency Counter
try:
    frequency_counter = FrequencyCounter(address="/dev/FREQCOUNT")
    frequency_counter.set_sample_time(1)
except:
    print("Could not initialize the Frequency counter")

# Trying to initialize the Koherons
try:
    kc1 = KoheronController("/dev/Koheron1")
except:
    print("Could not initialize Koheron 1")
try:
    kc2 = KoheronController("/dev/Koheron2")
except:
    print("Could not initialize Koheron 2")


# Trying to initialize the Arduinos:
try:
    ard1 = ArduinoCurrentLocker("/dev/Arduino1")
except:
    print("Could not initialize Arduino 1")
try:
    ard2 = ArduinoCurrentLocker("/dev/Arduino2")
except:
    print("Could not initialize Arduino 2")


# Opening the DataLog
try:
    DataLog = open("DataLog.txt","a+")
    DataLog.close()
except:
    DataLog = open("DataLog.txt","a+")
    DataLog.close()

try:
    log = open("logs.txt","a+")
    log.write("---------------------------------------------------------------------------------------------------------------\n")
except: 
    log = open("logs.txt","a+")
    log.write("---------------------------------------------------------------------------------------------------------------\n")
              
### Error Function
def error(message):
    try:
        log.write("Time: " + str(datetime.datetime.now()) + " ERROR: " + message + "\n")
        suffix = ""
    except:
        suffix = "Can not write to log"
    return "ERROR: " + message + " " + suffix + "\n"


### Function to get the Frequency Counter Readings
def freqCounter():
    try:
        rval = frequency_counter.get_frequency_and_range()
        if (rval[0]).casefold() == ("Signal").casefold() or (rval[1]).casefold() == ("Signal").casefold():
            rval = [0,0]
    except:
        rval = [0,0]
      
    return rval


    
### Function for associating a query to a given function and creating + sending the message
def associate(Data,conn):
    message = ""
    if (Data[0:4]).casefold() == ("Ping").casefold():
       message = "Pong"
       
    elif (Data[0:5]).casefold() == ("Temp?").casefold():
       try:
           temp = DualBME280s.temp()
           if temp[0] == 999: # Default output if a problem occurs 
               message = error("BME280A could not give the temperature")
           if temp[1] == 999: # Default output if a problem occurs 
               message += error("BME280B could not give the temperature")
           message += "Temperature: " + str(temp[0]) + ", " + str(temp[1])
       except:
           message = error("Could not connect to the BME280s")


    #TO-DO Need to add in the altitude reading from the Gondola
    elif (Data[0:4]).casefold() == ("Alt?").casefold():
        message = "Altitude is of Z"

    elif (Data[0:6]).casefold() == ("Humid?").casefold():
       try:
           humid = DualBME280s.humidity()
           if humid[0] == -1: #Default output if a problem occurs
               message = error("BME280A could not give the humidity")
           if humid[1] == -1: # Default output if a problem occurs 
               message += error("BME280B could not give the humidity")
           message += "Humidity: " + str(humid[0]) + ", " + str(humid[1])
       except:
           message = error("Could not connect to the BME280s")
    
    elif (Data[0:9]).casefold() == ("Pressure?").casefold():
        try:
            pressure = DualBME280s.pressure()
            if pressure[0] == -1:
                message = error("BME280A could not give the pressure")
            if pressure[1] == -1:
                message += error("BME280B could not give the pressure")
            message += "Pressure: " + str(pressure[0]) + ", " + str(pressure[1])
        except:
            message = error("Could not connect to the BME280s")

    #TO-DO: Optional, may or may not add this coordinate feature depending on the data received and if it is feasible NOT A PRIORITY AND CAN BE DEPRICATED
    elif (Data[0:4]).casefold() == ("Loc?").casefold():
        message = "X: XPLACEHOLDER" + " " + "Y: YPLACEHOLDER" + " " + "Z: ZPLACEGOLDER"
            
    elif (Data[0:10]).casefold() == ("Frequency?").casefold():
        freq = freqCounter() 
        if freq == [0,0]:
            message = error("Frequency Counter could not give Frequency and Range, defaulted at 0") # Not throwing an error, since the FreqCounter is already doing so, only adding a message for the user to read
        message += "Frequency is of: " + str(freq[1]) + " MHz"
            
    elif (Data[0:3]).casefold() == ("ard").casefold():
        if (Data[3]).casefold() == ("1").casefold():
            if (Data[4:21]).casefold() == (".default_params()").casefold():
                try:
                    ard1.default_params()
                    message = "Default Params have been set for Arduino 1"
                except:
                     message = error("Could not set Default Params for Arduino 1")                
            
            elif (Data[4:10]).casefold() == (".idn()").casefold():
                try:
                    idNum = ard1.idn
                    message = "Arduino 1's ID Number is: " + str(idNum)
                except:
                    message = error("Could not get the ID number from Arduino 1")
                        

            elif (Data[4:23]).casefold() == (".load_from_eeprom()").casefold():
                try:
                    ard1.load_from_eeprom()
                    message += "Arduino 1 Loaded from EEPROM"
                except:
                    message = error("Could not load from EEPROM for Arduino 1")

               
            elif (Data[4:]).casefold() == (".save_to_eeprom()").casefold():
                try:
                    ard1.save_to_eeprom()
                    message = "Arduinon 1's settings Saved to EEPROM"
                except:
                    message = error("Could not Save Arduino 1's settings to EEPROM")
                
            elif (Data[4:]).casefold() == (".get_params()").casefold():
                try:
                    params = ard1.get_params()
                    message = "Params are" + str(params)
                except:
                    message = error("Could not get Params of Arduino 1")

            elif (Data[4:]).casefold() == (".set_params()").casefold():
                try:
                    rval = ard1.set_params()
                    message = rval
                except:
                    message = error("Could not set the Params of Arduino 1")

            elif (Data[4:20]).casefold() == (".set_scan_state(").casefold():
                try:
                    state = Data[20:len(Data)-1]
                    ard1.set_scan_state(state)
                    message = "Scan State of Arduino 1 has been set to " + str(state)
                except:
                    message = error("Could not set Scan State of Arduino 1")

            elif (Data[4:]).casefold() == (".get_data()").casefold():
                try:
                    data = ard1.get_data()
                    message = "Arduino 1's Data is: " + str(data)
                except:
                    message = error("Could not get Arduino 1's Data")

            elif (Data[4:]).casefold() == (".get_sampling_rate()").casefold():
                try:
                    samplingRate = ard1.get_sampling_rate()
                    message = samplingRate
                except:
                    message = error("Could not get Arduino 1's sampling rate")

            elif (Data[4:]).casefold() == (".close()").casefold():
                try:
                    ard1.close()
                    message = "Arduino 1 has been closed"
                except:
                    message = error("Arduino 1 was not closed")

            elif (Data[4:]).casefold() == (".print_params()").casefold():
                try:
                    params = ard1.print_params()
                    message = "Arduino 1's Params are:\n" + params
                except:
                    message = error("Arduino 1's params could not be accessed")

            elif (Data[4:14]).casefold() == (".scan_amp(").casefold():
                try:
                    amp = Data[14:len(Data)-1]
                    flAmp = float(amp)
                    ard1.scan_amp(flAmp)
                    message = "Scan Amp has been set"
                except ValueError as e:
                    message = error("No float Value detected in function call: " + str(e))
                except:
                    message = error("Could not set the Scan Amplitude of Arduino 1")
                    
            elif (Data[4:]).casefold() == (".lock()").casefold():
                try:
                    ard1.lock()
                    message = "Arduino 1 has been Locked"
                except:
                    message = error("Arduino 1 could not be locked")

            elif (Data[4:]).casefold() == (".unlock()").casefold():
                try:
                    ard1.unlock()
                    message = "Arduino 1 has been Unlocked"
                except:
                    message = error("Arduino 1 could not be unlocked")

            elif (Data[4:12]).casefold() == (".gain_p(").casefold():
                try:
                    pgain = Data[12:len(Data)-1]
                    flPgain = float(pgain)
                    message = ard1.gain_p(flPgain)
                except ValueError as e:
                    message = error("No Float value detected in function call: " + str(e))
                except:
                    message = error("Could not set pgain of Arduino 1")


            elif (Data[4:12]).casefold() == (".gain_i(").casefold():
                try:
                    igain = Data[12:len(Data)-1]
                    flIgain = float(igain)
                    message = ard1.gain_i(flIgain)
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set igain of Arduino 1")

            elif (Data[4:13]).casefold() == (".gain_i2(").casefold():
                try:
                    i2gain = Data[13:len(Data)-1]
                    flI2gain = float(i2gain)
                    message =  ard1.gain_i2(flI2gain)
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set i2gain of Arduino 1")


            elif (Data[4:19]).casefold() == (".output_offset(").casefold():
                try:
                    offset = Data[19:len(Data)-1]
                    flOffset = float(offset)
                    ard1.output_offset(flOffset)
                    message = "Arduino 1's Offset has been set"
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set offset of Arduino 1")

            elif (Data[4:]).casefold() == (".increase_offset()").casefold():
                try:
                    ard1.increase_offset()
                    message = "Arduino 1's Offset has sucessfully been Increased"
                except:
                    message = error("Arduino 1's Offset has failed to increase")

            elif (Data[4:]).casefold() == (".decrease_offset()").casefold():
                try:
                    ard1.dectrase_offset()
                    message = "Arduino 1's offset has sucessfully beenDecreased"
                except:
                    message = error("Arduino 1's offset has failed to decrease")

            elif (Data[4:10]).casefold() == (".fwhm(").casefold():
                try:
                    fwhm = Data[10:len(Data)-1]
                    flFwhm = float(fwhm)
                    ard1.fwhm(flFwhm)
                    message = "Arduino 1's FWHM has been set"
                except:
                    message = error("Could not set Arduino 1's FWHM")

            elif (Data[4:16]).casefold() ==  (".n_averages(").casefold():
                try:
                    n = Data[16:len(Data)-1]
                    flN = float(n)
                    ard1.n_averages(flN)
                    message = "Arduino 1's N Averages has been set"
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set Arduino 1's N_averages")

            elif (Data[4:14]).casefold() == (".low_pass(").casefold():
                try:
                    lp = Data[14:len(Data)-1]
                    inLp = float(lp)
                    message = ard1.low_pass(inLp)
                except ValueError as e:
                    message = error("No int value detected in the function call: " + str(e))
                except:
                    message = error("Could not set Arduino 1's Low Pass Cutoff")

                
        elif (Data[3]).casefold() == ("2").casefold():
            if (Data[4:21]).casefold() == (".default_params()").casefold():
                try:
                    ard2.default_params()
                    message = "Default Params have been set for Arduino 2"
                except:
                     message = error("Could not set Default Params for Arduino 2")                
            
            elif (Data[4:10]).casefold() == (".idn()").casefold():
                try:
                    idNum = ard2.idn
                    message = "Arduino 2's ID Number is: " + str(idNum)
                except:
                    message = error("Could not get the ID number from Arduino 2")
                        

            elif (Data[4:23]).casefold() == (".load_from_eeprom()").casefold():
                try:
                    ard2.load_from_eeprom()
                    message += "Arduino 2 Loaded from EEPROM"
                except:
                    message = error("Could not load from EEPROM for Arduino 2")

               
            elif (Data[4:]).casefold() == (".save_to_eeprom()").casefold():
                try:
                    ard2.save_to_eeprom()
                    message = "Arduinon 2's settings Saved to EEPROM"
                except:
                    message = error("Could not Save Arduino 2's settings to EEPROM")
                
            elif (Data[4:]).casefold() == (".get_params()").casefold():
                try:
                    params = ard2.get_params()
                    message = "Params are" + str(params)
                except:
                    message = error("Could not get Params of Arduino 2")

            elif (Data[4:]).casefold() == (".set_params()").casefold():
                try:
                    rval = ard2.set_params()
                    message = rval
                except:
                    message = error("Could not set the Params of Arduino 2")

            elif (Data[4:20]).casefold() == (".set_scan_state(").casefold():
                try:
                    state = Data[20:len(Data)-1]
                    ard2.set_scan_state(state)
                    message = "Scan State of Arduino 2 has been set to " + str(state)
                except:
                    message = error("Could not set Scan State of Arduino 2")

            elif (Data[4:]).casefold() == (".get_data()").casefold():
                try:
                    data = ard2.get_data()
                    message = "Arduino 2's Data is: " + str(data)
                except:
                    message = error("Could not get Arduino 2's Data")

            elif (Data[4:]).casefold() == (".get_sampling_rate()").casefold():
                try:
                    samplingRate = ard2.get_sampling_rate()
                    message = samplingRate
                except:
                    message = error("Could not get Arduino 2's sampling rate")

            elif (Data[4:]).casefold() == (".close()").casefold():
                try:
                    ard2.close()
                    message = "Arduino 2 has been closed"
                except:
                    message = error("Arduino 2 was not closed")

            elif (Data[4:]).casefold() == (".print_params()").casefold():
                try:
                    params = ard2.print_params()
                    message = "Arduino 2's Params are:\n" + params
                except:
                    message = error("Arduino 2's params could not be accessed")

            elif (Data[4:14]).casefold() == (".scan_amp(").casefold():
                try:
                    amp = Data[14:len(Data)-1]
                    flAmp = float(amp)
                    ard2.scan_amp(flAmp)
                    message = "Scan Amp has been set"
                except ValueError as e:
                    message = error("No float Value detected in function call: " + str(e))
                except:
                    message = error("Could not set the Scan Amplitude of Arduino 2")
                    
            elif (Data[4:]).casefold() == (".lock()").casefold():
                try:
                    ard2.lock()
                    message = "Arduino 2 has been Locked"
                except:
                    message = error("Arduino 2 could not be locked")

            elif (Data[4:]).casefold() == (".unlock()").casefold():
                try:
                    ard2.unlock()
                    message = "Arduino 2 has been Unlocked"
                except:
                    message = error("Arduino 2 could not be unlocked")

            elif (Data[4:12]).casefold() == (".gain_p(").casefold():
                try:
                    pgain = Data[12:len(Data)-1]
                    flPgain = float(pgain)
                    message = ard2.gain_p(flPgain)
                except ValueError as e:
                    message = error("No Float value detected in function call: " + str(e))
                except:
                    message = error("Could not set pgain of Arduino 2")


            elif (Data[4:12]).casefold() == (".gain_i(").casefold():
                try:
                    igain = Data[12:len(Data)-1]
                    flIgain = float(igain)
                    message = ard2.gain_i(flIgain)
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set igain of Arduino 2")

            elif (Data[4:13]).casefold() == (".gain_i2(").casefold():
                try:
                    i2gain = Data[13:len(Data)-1]
                    flI2gain = float(i2gain)
                    message =  ard2.gain_i2(flI2gain)
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set i2gain of Arduino 2")


            elif (Data[4:19]).casefold() == (".output_offset(").casefold():
                try:
                    offset = Data[19:len(Data)-1]
                    flOffset = float(offset)
                    ard2.output_offset(flOffset)
                    message = "Arduino 2's Offset has been set"
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set offset of Arduino 2")

            elif (Data[4:]).casefold() == (".increase_offset()").casefold():
                try:
                    ard2.increase_offset()
                    message = "Arduino 2's Offset has sucessfully been Increased"
                except:
                    message = error("Arduino 2's Offset has failed to increase")

            elif (Data[4:]).casefold() == (".decrease_offset()").casefold():
                try:
                    ard2.dectrase_offset()
                    message = "Arduino 2's offset has sucessfully beenDecreased"
                except:
                    message = error("Arduino 2's offset has failed to decrease")

            elif (Data[4:10]).casefold() == (".fwhm(").casefold():
                try:
                    fwhm = Data[10:len(Data)-1]
                    flFwhm = float(fwhm)
                    ard2.fwhm(flFwhm)
                    message = "Arduino 2's FWHM has been set"
                except:
                    message = error("Could not set Arduino 2's FWHM")

            elif (Data[4:16]).casefold() ==  (".n_averages(").casefold():
                try:
                    n = Data[16:len(Data)-1]
                    flN = float(n)
                    ard2.n_averages(flN)
                    message = "Arduino 2's N Averages has been set"
                except ValueError as e:
                    message = error("No float value detected in function call: " + str(e))
                except:
                    message = error("Could not set Arduino 2's N_averages")

            elif (Data[4:14]).casefold() == (".low_pass(").casefold():
                try:
                    lp = Data[14:len(Data)-1]
                    inLp = float(lp)
                    message = ard2.low_pass(inLp)
                except ValueError as e:
                    message = error("No int value detected in the function call: " + str(e))
                except:
                    message = error("Could not set Arduino 2's Low Pass Cutoff")
            
    elif (Data[0:9]).casefold() == ("get_temp(").casefold():
                try:
                    res = Data[9:len(Data)-1]
                    flRes = float(res)
                    temp = get_temp(flRes)
                    strTemp = str(temp)
                    message = "Temperature is of " + strTemp
                except:
                    message = error("Could not get the Temperature")


    elif (Data[0:15]).casefold() == ("get_resistance(").casefold():
                try:
                    temp = Data[15:len(Data)-1]
                    flTemp = float(temp)
                    res = get_resistance(temp)
                    strRes = str(res)
                    message = "The resistance is of: "+ strRes
                except:
                    message = error("Could not get the Resistance")   
                    
    elif (Data[0:2]).casefold() == ("kc").casefold():
        if (Data[2]).casefold() == ("1").casefold():
            if (Data[3:10]).casefold() == (".write(").casefold():
                try:
                    command = Data[10:len(Data)-1]
                    kc1.write(command)
                    message = "Koheron 1 wrote: " + command
                except:
                    message = error("Koheron 1 could not write the command")

            elif (Data[3:8]).casefold() == (".ask(").casefold():
                try:
                    command = Data[8:len(Data)-1]
                    message = "Response: " + str(kc1.ask(command))
                except:
                    message = error("Koheron 1 could not ask the query")

            elif (Data[3:9]).casefold() == (".close").casefold():
                try:
                    kc1.close()
                    message = "Koheron 1 has been Closed"
                except:
                    message = error("Could not close Koheron 1")

            elif (Data[3:13]).casefold() == (".set_temp(").casefold():
                try:
                    temp = Data[13:len(Data)-1]
                    flTemp = float(temp)
                    kc1.set_temp(flTemp)
                    message = "Temperature has been set to: " + temp
                except ValueError as e:
                    message = error("No float value detected in the function call: " + str(e))
                except:
                    message = error("Could not Set the Temperature of Koheron 1")

            elif (Data[3:17]).casefold() == (".read_set_temp").casefold():
                try:
                    temp = str(kc1.read_set_temp())
                    message = "Koheron 1's set Temperature is: " + temp
                except:
                    message = error("Could not read Koheron 1's Set Temp")

            elif (Data[3:13]).casefold() == (".read_temp").casefold():
                try:
                    temp = kc1.read_temp()
                    strTemp = str(temp)
                    message = "Temperature is:" + strTemp
                except:
                    message = error("Could not Read the Temperature of Koheron 1")

            elif (Data[3:16]).casefold() == (".set_current(").casefold():
                try:
                    curr = Data[16:len (Data)-1]
                    fltCurr = float(curr)
                    kc1.set_current(fltCurr) 
                    message = "Koheron 1's current has been set to: " + curr
                except ValueError as e:
                    message = error("No float value detected in the function call: " + str(e))
                except:
                    message = error("Could not set the Current of Koheron 1")


            elif (Data[3:12]).casefold() == (".laser_on").casefold():
                try:
                    kc1.laser_on()
                    message = "Koheron 1's Laser has been turned On"
                except:
                    message = error("Could not turn on Koheron 1's Laser")

            elif (Data[3:13]).casefold() == (".laser_off").casefold():
                try:
                    kc1.laser_off()
                    message = "Koheron 1's Laser has been turned off"
                except:
                    message = error("Could not turn off Koheron 1's Laser")

            elif (Data[3:16]).casefold() == (".read_current").casefold():
                try:
                    curr = kc1.read_current()
                    strCurr = str(curr)
                    message = "Koheron 1's Current is of: " + strCurr
                except:
                    message = error("Could not read Koheron 1's current")

            elif (Data[3:21]).casefold() == (".increase_current(").casefold():
                try:
                    adj = Data[21:len(Data)-1]
                    flAdj = float(adj)
                    kc1.increase_current(flAdj)
                    message = "Koheron 1's Current has been increased to: " + adj
                except:
                    message = error("Could not increase Koheron 1's current")

            elif (Data[3:21]).casefold() == (".decrease_current(").casefold():
                try:
                    adj = Data[21:len(Data)-1]
                    flAdj = float(adj)
                    kc1.decrease_current(flAdj)
                    message = "Koheron 1's Current has been decreased to: " + adj
                except:
                    message = error("Could not decrease Koheron 1's current")

            
            elif (Data[3:]).casefold() == (".stream_data()").casefold():
                try:
                    val = kc1.ask('rtact')
                    flVal = float(val)
                    temp = get_temp(flVal)

                    curr = kc1.ask('ilaser')
                    flCurr = float(curr)
                    if(float(kc1.ask('lason'))==1):
                        onoff = 'On'
                    else:
                        onoff = 'Off'
                    message = "Temperature: " + str(temp) + " C   Laser: " + onoff + "   Current: " + curr + " mA"
                except ValueError as e:
                    message = error("Parsing Error: " + str(e))
                except:
                    message = error("Could not stream Data from Koheron 1")

        elif (Data[2]).casefold() == ("2").casefold():
            if (Data[3:10]).casefold() == (".write(").casefold():
                try:
                    command = Data[10:len(Data)-1]
                    kc2.write(command)
                    message = "Koheron 2 wrote: " + command
                except:
                    message = error("Koheron 2 could not write the command")

            elif (Data[3:8]).casefold() == (".ask(").casefold():
                try:
                    command = Data[8:len(Data)-1]
                    message = "Response: " + str(kc2.ask(command))
                except:
                    message = error("Koheron 2 could not ask the query")

            elif (Data[3:9]).casefold() == (".close").casefold():
                try:
                    kc2.close()
                    message = "Koheron 2 has been Closed"
                except:
                    message = error("Could not close Koheron 2")

            elif (Data[3:13]).casefold() == (".set_temp(").casefold():
                try:
                    temp = Data[13:len(Data)-1]
                    flTemp = float(temp)
                    kc2.set_temp(flTemp)
                    message = "Temperature has been set to: " + temp
                except ValueError as e:
                    message = error("No float value detected in the function call: " + str(e))
                except:
                    message = error("Could not Set the Temperature of Koheron 2")

            elif (Data[3:17]).casefold() == (".read_set_temp").casefold():
                try:
                    temp = str(kc2.read_set_temp())
                    message = "Koheron 2's set Temperature is: " + temp
                except:
                    message = error("Could not read Koheron 2's Set Temp")

            elif (Data[3:13]).casefold() == (".read_temp").casefold():
                try:
                    temp = kc2.read_temp()
                    strTemp = str(temp)
                    message = "Temperature is:" + strTemp
                except:
                    message = error("Could not Read the Temperature of Koheron 2")

            elif (Data[3:16]).casefold() == (".set_current(").casefold():
                try:
                    curr = Data[16:len (Data)-1]
                    fltCurr = float(curr)
                    kc2.set_current(fltCurr) 
                    message = "Koheron 2's current has been set to: " + curr
                except ValueError as e:
                    message = error("No float value detected in the function call: " + str(e))
                except:
                    message = error("Could not set the Current of Koheron 2")


            elif (Data[3:12]).casefold() == (".laser_on").casefold():
                try:
                    kc2.laser_on()
                    message = "Koheron 2's Laser has been turned On"
                except:
                    message = error("Could not turn on Koheron 2's Laser")

            elif (Data[3:13]).casefold() == (".laser_off").casefold():
                try:
                    kc2.laser_off()
                    message = "Koheron 2's Laser has been turned off"
                except:
                    message = error("Could not turn off Koheron 2's Laser")

            elif (Data[3:16]).casefold() == (".read_current").casefold():
                try:
                    curr = kc2.read_current()
                    strCurr = str(curr)
                    message = "Koheron 2's Current is of: " + strCurr
                except:
                    message = error("Could not read Koheron 2's current")

            elif (Data[3:21]).casefold() == (".increase_current(").casefold():
                try:
                    adj = Data[21:len(Data)-1]
                    flAdj = float(adj)
                    kc2.increase_current(flAdj)
                    message = "Koheron 2's Current has been increased to: " + adj
                except:
                    message = error("Could not increase Koheron 2's current")

            elif (Data[3:21]).casefold() == (".decrease_current(").casefold():
                try:
                    adj = Data[21:len(Data)-1]
                    flAdj = float(adj)
                    kc2.decrease_current(flAdj)
                    message = "Koheron 2's Current has been decreased to: " + adj
                except:
                    message = error("Could not decrease Koheron 2's current")

            
            elif (Data[3:]).casefold() == (".stream_data()").casefold():
                try:
                    val = kc2.ask('rtact')
                    flVal = float(val)
                    temp = get_temp(flVal)

                    curr = kc2.ask('ilaser')
                    flCurr = float(curr)
                    if(float(kc2.ask('lason'))==1):
                        onoff = 'On'
                    else:
                        onoff = 'Off'
                    message = "Temperature: " + str(temp) + " C   Laser: " + onoff + "   Current: " + curr + " mA"
                except ValueError as e:
                    message = error("Parsing Error: " + str(e))
                except:
                    message = error("Could not stream Data from Koheron 2")

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
            print("Error in getting updates from arduinos")
            try:
                ArduinoLog.close()
            except:
                print("Already closed")
            return True
        
def connect():
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


        try:
            MCAST_GRP = '225.0.0.0'
            MCAST_PORT = 4446
            IS_ALL_GROUPS = False

            mCastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            #on this port, listen ONLY to MCAST_GRP
            mCastSocket.bind((MCAST_GRP, MCAST_PORT))

            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            mCastSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except:
            error("Could not connect to Multicast Group")

        return [d,dConn]


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
            d.listen()
            dConn, dAddr = d.accept()
            print("Connection at",dAddr)
        except:
            print("Data not Connected")
                
        #Give the connection a second
        time.sleep(1)


        try:
            MCAST_GRP = '225.0.0.0'
            MCAST_PORT = 4446
            IS_ALL_GROUPS = False

            mCastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            mCastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            #on this port, listen ONLY to MCAST_GRP
            mCastSocket.bind((MCAST_GRP, MCAST_PORT))

            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            mCastSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except:
            error("Could not connect to Multicast Group")
        ### Loop for the logged and sent data.
        ### Currently Logs: Temperature from both sensors, Frequency from the Frequency counter and the Local time.
        ### Needs to log time from RTC and Altitude of the Gondola (Waiting on CSA for that) 2019-08-02
            # [X] Sent them an email
            # [X] Received Example Code
            # [X] Implementing Example Code
            # [ ] Getting Jean-François to test the code


        RTCTime = ""
        altitude = "0"
        while True:
            DataLog = open("DataLog.txt","a+")
            message = ""
            try:
                prismMSG = (mCastSocket.recv(1024)).decode()
                prism_data = prismMSG.split(",")
                if prism_data[3] == "POS0":
                    RTCTime = str(prism_data[1])
                    altitude = str(prism_data[6])
                    #print(("Time: " + str(RTCTime) + "\tAltitude: " + altitude + "\n"), file=open("Prism_Time_and_Altitude_Data.txt", "a+"))
            except:
                RTCTime = str(datetime.datetime.now())
                altitude= "0"
            message = RTCTime + "\t" + altitude + "\t"
            try:
                temp = DualBME280s.temp()
                if temp[0] != 999:
                    message += str(temp[0])
                message += "\t"
                if temp[1] != 999:
                    message += str(temp[1])
                message += "\t"              
            except:
                message +="\t\t"

            try:
                freq = freqCounter()  
                message += str(freq[1]) + "\t"
            except:
                message += "0\t"
            message = message + "\n"

            try:
                DataLog.write(message)
                DataLog.close()
                dConn.sendto((message + "\r").encode(),dAddr)           
               
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
                try:
                    log = open("logs.txt","a+")
                    log.write("---------------------------------------------------------------------------------------------------------------\n")
                    log.write("Time: " + str(datetime.datetime.now()) + " Connected: " + str(addr) + "\n")        
                except:
                    log.write("Log already opened!\n")
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