import serial
import struct
import time
import numpy as np
from datetime import datetime
import os
#import zmq
import datetime
import sys
import threading


def ToVoltage(bits):
    return float((bits)/6553.6)

def ToBits(voltage):
    return int((voltage*6553.6))

ZEROV = 32768
V2P5 = 49512

params_default = (0.5, # ramp amplitude
                  0,0,0, #gain
                  ZEROV, #piezo output offset
                  1, #scan state
                  51.21, #ramp frequency
                  ToBits(-1.0)+ZEROV, #peak max voltage
                  0.612, #alpha
                  ToBits(-0.5)+ZEROV, #peak half max voltage
                  0)

params_struct_size = 4*11
params_struct_fmt = '<'+'ffffiififii'

"""
struct Params {
  float ramp_amplitude; //[0] 
  float p_gain, i_gain, i2_gain; //[1] [2] [3] 
  long output_offset; //[4]
  long scan_state; //[5]
  float ramp_frequency; //[6]
  long sig_peak_voltage; //[7]
  float alpha; //[8]
  long sig_half_max_voltage; //[9]
  long lock_type; // [10]
};
"""


# float ToVoltage(float bits) {
#   return (bits-32768)/6553.6;
# }

# float ToBits(float voltage) {
#   return voltage*6553.6+32768;
# }




class ArduinoLocker:
    """Control the arduino set up for laser locking.

    Requires:
    An arduino Uno microcontroller flashed with the .ino code
    """


    def __init__(self, serialport='/dev/ttyUSB1'):
        self.serialport = serialport
        self.ser = serial.Serial(serialport, baudrate=115200, timeout=2.0)
        print("Connection to Arduino established at port %s"%self.ser.name)
        time.sleep(4)  # wait for microcontroller to reboot
        self.ser.flushInput()
        self.ser.flushOutput()
        #self.params = list(self.get_params)
        #self.params = list(params_default)
        #self.set_params()
        self.get_params()
        time.sleep(0.1)
        self.print_params()
        self.listen = False
    
    
    def default_params(self):
        self.params = list(params_default)
        self.set_params()

    def load_from_eeprom(self):
        self.ser.write(b'r')
        self.unlock()

    def save_to_eeprom(self):
        self.ser.write(b'w')

    def get_params(self):
        """Get params structure from the microcontroller and store it locally."""
        write_string = b'g'
        self.ser.write(write_string)
        data = self.ser.read(params_struct_size)
        #print(data)
        data_tuple = struct.unpack(params_struct_fmt, data)
        #sanity check: sometimes the arduino returns garbage
        if(data_tuple[4]<65536 and data_tuple[4]>0 and data_tuple[5]<=1 and data_tuple[5]>=0):
            self.params = list(data_tuple)
            return data_tuple
        else:
            print("Inappropriate data fetched from arduino")
            self.set_params()
            return self.params
        return data_tuple

    def set_params(self):
        """Set params on the microcontroller."""
        data = struct.pack(params_struct_fmt, *self.params)
        self.ser.write(b's'+data)
        time.sleep(0.1)
        s = self.ser.readline()
        print(s)

    def set_scan_state(self,scan_state):
        self.params[5] = int(scan_state)
        self.set_params()

        
    # def get_data(self):
    #     s = self.ser.readline()
    #     try:
    #         err,corr = s.split(',')
    #         err = float(err)
    #         corr = float(corr)
    #     except:
    #         err = 0
    #         corr = 0
    #     return err,corr

        
    def get_sampling_rate(self):
        self.ser.write(b't')
        sampling_time = self.ser.readline()
        print("Loop period: %i us"%int(sampling_time))

    def close(self):
        self.ser.close()


    def print_params(self):
        self.get_params()
        """ Print the current parameters on the microcontroller. """
        print('Ramp amplitude = {0:.3f} V'.format(self.params[0]))
        print('Ramp frequency = {0:.3f} Hz'.format(self.params[6]))
        print("Output offset = {0:.3f} V".format(ToVoltage(self.params[4]-ZEROV)))
        print('Gain Parameters: P = {0:.3f}, I = {1:.3e}, I2 = {2:.3e}'.format(self.params[1],self.params[2],self.params[3]))
        print('Scan On/Off: {0:.0f}'.format(self.params[5]))
        print('Max voltage: {0:.2f} V'.format(ToVoltage(self.params[7]-ZEROV)))
        print("Half max voltage: %.3f"%(ToVoltage(self.params[9]-ZEROV)))
        print('Lock type: %i'%self.params[10])
    
    def lock_type(self,type):
        """Switch between side-of-fringe locking (0) and peak locking (1)"""
        if(type==0 or type==1):
            self.params[10] = type
            self.set_params()
    
    def scan_amp(self,new_amplitude):
        """Set scan amplitude on the microcontroller in Volts."""
        self.params[0] = new_amplitude
        self.set_params()
    
    def scan_freq(self,new_freq):
        """Set scan frequency on the microscontroller in Hz """
        self.params[6] = new_freq
        self.set_params()
        
    def set_sig_max_voltage(self,new_max):
        """Set the signal peak voltage (include the sign of the voltage)"""
        self.params[7] = ToBits(new_max)+ZEROV
        self.set_params()
        
    def set_sig_half_max_voltage(self,new_half_max):
        """Set the signal half max voltage (include the sign of the voltage)."""
        self.params[9] = ToBits(new_half_max)+ZEROV
        self.set_params()
        
    def lock(self):
        self.set_scan_state(0)
        self.get_params()
        print("Locked")
        print("Signal peak detected: %.3f"%(ToVoltage(self.params[7]-ZEROV)))
    
    
    def listener(self):
        while(self.listen):
            read_in = self.ser.readline()
            print(read_in)
    
    def unlock(self):
        self.set_scan_state(1)
        print("Unlocked - Scanning")

    def gain_p(self,new_gain):
        self.params[1] = new_gain
        self.set_params()
        print("Proportional gain updated to:" + str(new_gain))
        
    def gain_i(self,new_gain):
        self.params[2] = new_gain
        self.set_params()
        print("Integral gain updated to:" + str(new_gain))
        
    def gain_i2(self,new_gain):
        self.params[3] = new_gain
        self.set_params()
        print("Integral squared gain updated to:" + str(new_gain))
    
    
    def output_offset(self,offset):
        """ Set the piezo output offset in V """
        self.params[4] = int(ToBits(offset)+ZEROV)
        self.set_params()
    
    def increase_offset(self):
        self.params[4] += int(ToBits(0.1))
        self.set_params()
    
    def decrease_offset(self):
        self.params[4] -= int(ToBits(0.1))
        self.set_params()


    def low_pass(self,new_lp):
        """ Change low-pass cutoff frequency in Hz """
        del_t = 1e-6*(10.9*self.params[9]+20.6) #s
        rc = 1.0/new_lp
        alpha = del_t/(rc+del_t)
        self.params[10] = alpha
        self.set_params()
        print("Low-pass cutoff changed to %.0f Hz (alpha= %.3f)"%(new_lp,alpha))
        

