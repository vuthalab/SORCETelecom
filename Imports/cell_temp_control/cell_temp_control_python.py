import serial
import struct
import time
import numpy as np


# Valid R range (32,770 to 3.599) Ohms
a = 3.3540170e-03
b = 2.5617244e-04
c = 2.1400943e-06
d = -7.2405219e-08

# Valid T range (0 to 49) Ohms
A = -1.5470381e1
B = 5.6022839e3
C = -3.7886070e5
D = 2.4971623e7

def resis_to_temp(resistance):
    """Returns temperature in Degrees Celsius"""
    #Calculates thermistor resistance
    #Code for thermistor temperature calculation. Constants above and below as well as equation from https://www.thorlabs.com/_sd.cfm?fileName=4813-S01.pdf&partNumber=TH10K
    logarith = np.log(resistance/10000.0) #Logarithm required
    T = 1.0/(a + b * logarith + c * (logarith ** 2) + d * (logarith ** 3)) #Temperature calulcation
    return (T - 273.15)


def temp_to_resis(temp):
    """Returns resistance as a function of temperature in Degrees Celsius"""
    #Code for thermistor resistance calculation. Equation available: https://www.thorlabs.com/_sd.cfm?fileName=4813-S01.pdf&partNumber=TH10K
    tempC = temp + 273.15
    Rth = (10000.0)*np.exp(A + B/tempC + C/(tempC ** 2) + D/(tempC ** 3)) #Thermistor resistance
    #Voltage calculation 
    return Rth

ZEROV = 2**15

"""

struct Params {
  unsigned int enable0;
  unsigned int set_temp0;
  float prop_gain0;
  float pi_pole0;
  float pd_pole0;

  unsigned int enable1;
  unsigned int set_temp1;
  float prop_gain1;
  float pi_pole1;
  float pd_pole1;

};


struct Logger {
  unsigned int gate_voltage0;
  unsigned int gate_voltage1;

  int error_signal0;
  int error_signal1;

};

"""

params_struct_size = 2*4 + 4*6
params_struct_fmt = '<HHfffHHfff'

logger_struct_size = 2*2 + 4*5
logger_struct_fmt = '<HHfffff'


params_default = (0,
                  ZEROV,
                  0,
                  0,
                  0,
                  0,
                  20,
                  0,
                  0,
                  0)

class DualUnipolarTemperatureController:

    def __init__(self, serialport='COM15'):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, baudrate=115200)
        self.params = list(params_default)
        self.set_params(self.params)


    def get_params(self):
        write_string = b'g'
        self.ser.write(write_string)
        data = self.ser.read(params_struct_size)
        data_tuple = struct.unpack(params_struct_fmt, data)
        return data_tuple

    def get_logger(self):
        write_string = b'l'
        self.ser.write(write_string)
        data = self.ser.read(logger_struct_size)
        data_tuple = struct.unpack(logger_struct_fmt, data)
        return data_tuple

    def set_params(self, data_tuple):
        write_string = b's'
        self.ser.write(write_string)
        data = struct.pack(params_struct_fmt, *data_tuple)
        self.ser.write(data)

    def set_temp(self,temp):
        kohms = temp_to_resis(temp)*1e-3
        set_v_dac = int((kohms - 10.)/(kohms + 10.)*ZEROV + ZEROV)
        return set_v_dac

    def get_temp(self):
        temp_logger = self.get_logger()
        v_read = temp_logger[2]
        #v_read = float(read_temp - ZEROV)/ZEROV
        return (1.+v_read)/(1.-v_read)*10
        #return resis_to_temp(set_resist*1e3)
        
        
    
    def load_from_eeprom(self):
        self.ser.write(b'r')

    def save_to_eeprom(self):
        self.ser.write(b'w')

    def close(self):
        self.ser.close()


dutc = DualUnipolarTemperatureController(serialport='/dev/ttyACM0')

#if __name__ == '__main__':
#    dutc = DualUnipolarTemperatureController()
