import serial
import struct
import time
import numpy as np
import os
from datetime import datetime

#os.chdir('/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/data/intensity fluctuation test')

ZEROV = 2**15

def toVoltage(bits):
    return (bits-32768)/6553.6

def toBits(voltage):
    return voltage*6553.6+32768
    
class PhotodiodeMonitor:
    def __init__(self, serialport='/dev/ttyACM2'):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, baudrate=115200, timeout=2.0)
        print("Connection to Arduino established at port %s"%self.ser.name)
        time.sleep(4)  # wait for microcontroller to reboot
        self.ser.flushInput()
        self.ser.flushOutput()
        #self.params = Params()
        #self.get_params()
        #self.print_params()
        
    def get_monitor(self):
        variable = self.ser.readline()
        variable_new = variable.strip(b'\r\n').decode()    
        try:    
            err2,err1,corr2,corr1=variable_new.split(",")
            err2 = toVoltage(float(err2))
            err1 = toVoltage(float(err1))
            corr2 = toVoltage(float(corr2))
            corr1 = toVoltage(float(corr1))
        except:
            err2,err1,corr2,corr1 = 99,99,99,99
        return err1,err2,corr1,corr2
    
    def log_pd(self):
        
        now = datetime.fromtimestamp(time.time())
        time_stamp = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+":"+str(now.minute)+":"+str(now.second)

        fname = 'photodiode monitor'
        filepath = os.path.join(fname+'_'+time_stamp+'.txt')

        start_time = time.time()
        while(True):
            fp = open(filepath, 'a+')
            try:
                #now = datetime.fromtimestamp(time.time())
                now = time.time()
                variable = self.ser.readline()
                variable_new = variable.strip(b'\r\n').decode()
                
                err2,err1,corr2,corr1=variable_new.split(",")
                err2 = toVoltage(float(err2))
                err1 = toVoltage(float(err1))
                corr2 = toVoltage(float(corr2))
                corr1 = toVoltage(float(corr1))
                
                #pd1_v = toVoltage(pd1)
                #pd2_v = toVoltage(pd2)
                
                #new_line = str(now.hour)+':'+str(now.minute)+":"+str(now.second)+','+str(pd1_v)+','+str(pd2_v)
                new_line = str(now)+','+str(err1)+','+str(err2)+','+str(corr1)+','+str(corr2)
                print(new_line)
                fp.write(new_line+'\n')
                time.sleep(0.5)
            except(KeyboardInterrupt):
                break
            except:
                fp.write('error\n')
                pass
            fp.close()
        
