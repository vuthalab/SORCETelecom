import serial
import struct
import time
from datetime import datetime
import numpy as np
import os


#os.chdir('/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/data/intensity fluctuation test')

def resis_to_temp(resistance):
    """Returns temperature in Degrees Celsius"""
    # Valid R range (32,770 to 3.599) Ohms
    a = 3.3540170e-03
    b = 2.5617244e-04
    c = 2.1400943e-06
    d = -7.2405219e-08

    #Calculates thermistor resistance
    #Code for thermistor temperature calculation. Constants above and below as well as equation from https://www.thorlabs.com/_sd.cfm?fileName=4813-S01.pdf&partNumber=TH10K
    logarith = np.log(resistance/10000.0) #Logarithm required
    T = 1.0/(a + b * logarith + c * (logarith ** 2) + d * (logarith ** 3)) #Temperature calulcation
    return (T - 273.15)


def temp_to_resis(temp):
    """Returns resistance as a function of temperature in Degrees Celsius"""
    # Valid T range (0 to 49) Ohms
    A = -1.5470381e1
    B = 5.6022839e3
    C = -3.7886070e5
    D = 2.4971623e7

    #Code for thermistor resistance calculation. Equation available: https://www.thorlabs.com/_sd.cfm?fileName=4813-S01.pdf&partNumber=TH10K
    tempC = temp + 273.15
    Rth = (10000.0)*np.exp(A + B/tempC + C/(tempC ** 2) + D/(tempC ** 3)) #Thermistor resistance
    #Voltage calculation 
    return Rth

ZEROV = 2**15

def toVoltage(bits):
    return (bits-32768)/6553.6

def toBits(voltage):
    return int(voltage*6553.6+32768)
    
class Params:
    def __init__(self,enable,set_temp,p_gain,i_gain, i_rolloff, d_gain, output):
        self.enable = enable
        self.set_temp = set_temp
        self.p_gain = p_gain
        self.i_gain = i_gain
        self.i_rolloff = i_rolloff
        self.d_gain = d_gain
        self.output = output

"""

struct Logger {
  long temp_0;
  long temp_1;
};

"""

params_struct_fmt = '<iifffff'
params_struct_size = struct.calcsize(params_struct_fmt)

logger_struct_fmt = '<ii'
logger_struct_size = struct.calcsize(logger_struct_fmt)


class VicorTrimTemperatureController:

    def __init__(self, serialport='COM15'):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, baudrate=115200)
        self.ser.flushInput()
        self.ser.flushOutput()
        time.sleep(2)
        params_default2,params_default1 = self.get_params()

        self.params2 = Params(*params_default2)
        self.params1 = Params(*params_default1)

    def pack_params(self):
        p0 = [
            self.params2.enable,
            self.params2.set_temp,
            self.params2.p_gain,
            self.params2.i_gain,
            self.params2.i_rolloff,
            self.params2.d_gain,
            self.params2.output
        ]
        p1 = [
            self.params1.enable,
            self.params1.set_temp,
            self.params1.p_gain,
            self.params1.i_gain,
            self.params2.i_rolloff,
            self.params2.d_gain,
            self.params1.output
        ]
        return p0,p1
        
    def unpack_params(params_class,params_list):
        params_class.enable = params_list[0]
        params_class.set_temp = params_list[1]
        params_class.p_gain = params_list[2]
        params_class.i_gain = params_list[3]
        params_class.i_rolloff = params_list[4]
        params_class.d_gain = params_list[5]
        params_class.output = params_list[6]
    
    def get_params(self):
        """ returns packed params """
        write_string = b'g'
        self.ser.write(write_string)
        data0 = self.ser.read(params_struct_size)
        data1 = self.ser.read(params_struct_size)
        data_tuple0 = struct.unpack(params_struct_fmt, data0)
        data_tuple1 = struct.unpack(params_struct_fmt, data1)
        return data_tuple0,data_tuple1

    def get_logger(self):
        write_string = b'l'
        self.ser.write(write_string)
        data = self.ser.read(logger_struct_size)
        data_tuple = struct.unpack(logger_struct_fmt, data)
        return data_tuple

    def set_params(self):
        write_string = b's'
        self.ser.write(write_string)
        p0,p1 = self.pack_params()
        data = struct.pack(params_struct_fmt, *p0)
        self.ser.write(data)
        data = struct.pack(params_struct_fmt, *p1)
        self.ser.write(data)

    def get_temp(self):
        temp_logger = self.get_logger()
        V0 = (temp_logger[0]-ZEROV)/6553.6
        V1 = (temp_logger[1]-ZEROV)/6553.6
        R0 = (10e3*V0/(5-V0))
        R1 = (10e3*V1/(5-V1))
        #return V0,V1
        return resis_to_temp(R0),resis_to_temp(R1)
        
    def stream_temp(self):
        while(True):
            try:
                t2,t1 = self.get_temp()
                print("T2: %.3f C,    T1: %.3f C"%(t1,t2))
                time.sleep(1)
            except(KeyboardInterrupt):
                break
    
    
    
    def log_temp(self):
        now = datetime.fromtimestamp(time.time())
        time_stamp = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+":"+str(now.minute)+":"+str(now.second)

        fname = 'cell temperature'
        filepath = os.path.join(fname+'_'+time_stamp+'.txt')

        start_time = time.time()
        while(True):
            fp = open(filepath, 'a+')
            try:
                #now = datetime.fromtimestamp(time.time()) 
                now = time.time()
                t1,t2=self.get_temp()
                #new_line = str(now.hour)+':'+str(now.minute)+":"+str(now.second)+','+str(t1)+','+str(t2)
                new_line = str(now)+','+str(t1)+','+str(t2)
                print(new_line)
                fp.write(new_line+'\n')
                time.sleep(1.0)
            except(KeyboardInterrupt):
                break
            except:
                fp.write('error\n')
                pass
            fp.close()
        
    def set_temp(self,temp):
        kohms = temp_to_resis(temp)*1e-3
        volts = kohms*(5/(10+kohms))
        return toBits(volts)

    def set_output2(self,output):
        """output in volts between 0-15 V"""
        ard_output = 1.23*(output/15)
        self.params2.output = ard_output
        self.set_params()

    def set2(self,temp):
        bits = self.set_temp(temp)
        self.params2.set_temp = int(bits)
        self.set_params()
        
    def enable2(self):
        self.params2.enable = 1
        self.set_params()
    
    def disable2(self):
        self.params2.enable = 0
        self.set_params()
    
    def p_gain2(self,new_p):
        self.params2.p_gain = new_p
        self.set_params()
    
    def i_gain2(self,new_i):
        self.params2.i_gain = new_i
        self.set_params()
    
    def i_rolloff2(self, new_rolloff):
        self.params2.i_rolloff = new_rolloff
        self.set_params()
    
    def set_output1(self,output):
        """output in volts between 0-15 V"""
        ard_output = 1.23*(output/15)
        self.params1.output = ard_output
        self.set_params()
    
    def set1(self,temp):
        bits = self.set_temp(temp)
        self.params1.set_temp = bits
        self.set_params()
        
    def enable1(self):
        self.params1.enable = 1
        self.set_params()
    
    def disable1(self):
        self.params1.enable = 0
        self.set_params()
    
    def p_gain1(self,new_p):
        self.params1.p_gain = new_p
        self.set_params()
    
    def i_gain1(self,new_i):
        self.params1.i_gain = new_i
        self.set_params()
        
    def i_rolloff1(self, new_rolloff):
        self.params1.i_rolloff = new_rolloff
        self.set_params()
    
    def load_from_eeprom(self):
        self.ser.write(b'r')

    def save_to_eeprom(self):
        self.ser.write(b'w')

    def close(self):
        self.ser.close()
