import serial
import struct
import numpy as np
import time
import os
import threading

def ToVoltage(bits):
    return float((bits)/6553.6)

def ToBits(voltage):
    return int((voltage*6553.6))

ZEROV = 32768

"""
struct Params {
  long scan_state; //[0]
  float ramp_amplitude; //[1] V
  float ramp_frequency; //[2] Hz
  float output_offset; //[3] bits
  float p_gain, i_gain, i2_gain; //[4] [5] [6] 
  float alpha; //[7]
  float jump_voltage; //[8]
  float pmt_gain_voltage; //[9]
};
"""

class Params():
    def __init__(self, scan_state=0, ramp_amplitude=0.25,ramp_frequency=50.0,output_offset=0.0,p_gain=0.0,i_gain=0.0,i2_gain=0.0,alpha=0.05,jump_voltage=0,pmt_gain = 0.5):
        self.scan_state = scan_state
        self.ramp_amplitude = ramp_amplitude
        self.ramp_frequency = ramp_frequency
        self.output_offset = output_offset
        self.p_gain = p_gain
        self.i_gain = i_gain
        self.i2_gain = i2_gain
        self.alpha = alpha
        self.jump_voltage = jump_voltage
        self.pmt_gain = pmt_gain


params_struct_size = 4*10
params_struct_fmt = '<'+'ifffffffff' #little endian, followed by int, float, float, etc.
params_np_fmt = (int,float,float,float,float,float,float,float,float)
    


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
        self.params = Params()
        self.get_params()
        self.print_params()
        self.listen = False
        
    def save_params(self):
        fname = 'ard'+self.serialport[-1]+'_peak_settings.txt'
        filepath = '/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/code/SORCE control/'+fname
        fp = open(filepath, 'w')
        params_list = self.pack_params()
        for i in params_list:
            fp.write(str(i)+'\n')
        fp.close()

    def load_params(self):
        fname = 'ard'+self.serialport[-1]+'_peak_settings.txt'
        filepath = '/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/code/SORCE control/'+fname
        fp = open(filepath, 'r')
        
        params_list = tuple(np.genfromtxt(fp))
        fp.close()
        self.unpack_params(params_list)
        self.set_params()
        self.unlock()
        
    def load_from_eeprom(self):
        self.ser.write(b'r')
        self.unlock()

    def save_to_eeprom(self):
        self.ser.write(b'w')

    def get_params(self):
        """Get params structure from the microcontroller and store it locally."""
        self.ser.write(b'g')
        data = self.ser.read(params_struct_size)
        data_tuple = struct.unpack(params_struct_fmt, data)
        #sanity check: sometimes the arduino returns garbage
        if(data_tuple[0]<=1 and data_tuple[0]>=0):
            self.unpack_params(data_tuple)
        else:
            print("Inappropriate data fetched from arduino")
            self.set_params()
        return data_tuple

    def unpack_params(self,paramslist):
        """ Unpack the data received from the arduino and store it in the local params class"""
        self.params.scan_state = int(paramslist[0])
        self.params.ramp_amplitude = paramslist[1]
        self.params.ramp_frequency = paramslist[2]
        self.params.output_offset = paramslist[3]
        self.params.p_gain = paramslist[4]
        self.params.i_gain = paramslist[5]
        self.params.i2_gain = paramslist[6]
        self.params.alpha = paramslist[7]
        self.params.jump_voltage = paramslist[8]
        self.params.pmt_gain = paramslist[9]
        
    def pack_params(self):
        """ Pack the parameters from the local params class into a list to sent to the microcontroller"""
        data_tuple = (self.params.scan_state,self.params.ramp_amplitude,self.params.ramp_frequency,self.params.output_offset,self.params.p_gain,self.params.i_gain,self.params.i2_gain,self.params.alpha,self.params.jump_voltage,self.params.pmt_gain)
        return data_tuple
        
    def set_params(self):
        """Set params on the microcontroller to match the local params class."""
        data_tuple = self.pack_params()
        data = struct.pack(params_struct_fmt, *data_tuple)
        self.ser.write(b's'+data)
        time.sleep(0.2)
        s = self.ser.readline()
        print(s)

    def set_scan_state(self,scan_state):
        self.params.scan_state = int(scan_state)
        self.set_params()

        
    def get_sampling_rate(self):
        self.ser.write(b't')
        sampling_time = self.ser.readline()
        print("Loop period: %i us"%int(sampling_time))

    def close(self):
        self.ser.close()

    def print_params(self):
        self.get_params()
        """ Print the current parameters on the microcontroller. """
        print('Ramp amplitude = {0:.3f} V'.format(self.params.ramp_amplitude))
        print('Ramp frequency = {0:.3f} Hz'.format(self.params.ramp_frequency))
        print("Output offset = {0:.3f} V".format(self.params.output_offset))
        print('Gain Parameters: P = {0:.3f}, I = {1:.3e}, I2 = {2:.3e}'.format(self.params.p_gain,self.params.i_gain,self.params.i2_gain))
        print('Low pass filtering constant alpha = %.3f'%self.params.alpha)
        print("")
        print('Scan On/Off: {0:.0f}'.format(self.params.scan_state))
        print("Jump_voltage: %0.3f"%self.params.jump_voltage)
        print("PMT Gain voltage: %0.3f V"%self.params.pmt_gain)
        
    def get_string_params(self):
        self.get_params()
        """ Print the current parameters on the microcontroller. """
        msg += 'Ramp amplitude = {0:.3f} V'.format(self.params.ramp_amplitude) +"\n"
        msg += 'Ramp frequency = {0:.3f} Hz'.format(self.params.ramp_frequency) + "\n"
        msg += "Output offset = {0:.3f} V".format(self.params.output_offset) + "\n"
        msg += 'Gain Parameters: P = {0:.3f}, I = {1:.3e}, I2 = {2:.3e}'.format(self.params.p_gain,self.params.i_gain,self.params.i2_gain) + "\n"
        msg += 'Low pass filtering constant alpha = %.3f'%self.params.alpha + "\n"
        msg += "\n"
        msg += 'Scan On/Off: {0:.0f}'.format(self.params.scan_state) + "\n"
        msg += "Jump_voltage: %0.3f"%self.params.jump_voltage+ "\n"
        msg += "PMT Gain voltage: %0.3f V"%self.params.pmt_gain + "\n"
        return msg
    
    
    def scan_amp(self,new_amplitude):
        """Set scan amplitude on the microcontroller in Volts."""
        self.params.ramp_amplitude = new_amplitude
        self.set_params()
    
    def scan_freq(self,new_freq):
        """Set scan frequency on the microscontroller in Hz """
        self.params.ramp_frequency = new_freq
        self.set_params()
        
    def lock(self):
        """ Lock the laser"""
        self.set_scan_state(0)
        time.sleep(0.1)
        #lock_point = self.ser.readline()
        self.get_params()
        print("Locked")
        #print("Lock-point: %.3f V"%(ToVoltage(float(lock_point)-ZEROV)))
        #self.listen = True
        #listen_thread = threading.Thread(target=self.listener)
        #listen_thread.start()
    
    # def listener(self):
    #     while(self.listen):
    #         read_in = self.ser.readline()
    #         str_in = read_in.decode()
    #         print(str_in)
    #         if(str_in == 'testing'):
    #             self.unlock()
    #             self.listen=False
    #         time.sleep(1.0)
    
    def unlock(self):
        """ Unlock the laser and return to scan mode"""
        self.set_scan_state(1)
        print("Unlocked - Scanning")
        #self.listen = False

    def gain_p(self,new_gain):
        self.params.p_gain = new_gain
        self.set_params()
        print("Proportional gain updated to:" + str(new_gain))
        
    def gain_i(self,new_gain):
        self.params.i_gain = new_gain
        self.set_params()
        print("Integral gain updated to:" + str(new_gain))
        
    def gain_i2(self,new_gain):
        self.params.i2_gain = new_gain
        self.set_params()
        print("Integral squared gain updated to:" + str(new_gain))
    
    def output_offset(self,offset):
        """ Set the output offset in V """
        self.params.output_offset = int(ToBits(offset)+ZEROV)
        self.set_params()
    
    def increase_offset(self):
        """ Increase output offset by 10 mV """
        self.params.output_offset += 0.01
        self.set_params()
    
    def decrease_offset(self):
        """ Decrease output offset by 10 mV """
        self.params.output_offset -= 0.01
        self.set_params()

    def alpha(self,new_alpha):
        """ Change low pass filter constant alpha """
        self.params.alpha = new_alpha
        self.set_params();
        
    def set_jump_voltage(self,new_jump_voltage):
        self.params.jump_voltage = new_jump_voltage
        self.set_params()
        
    def pmt_gain(self,new_gain):
        self.params.pmt_gain = new_gain
        self.set_params()

        

#ard2 = ArduinoLocker(serialport='/dev/Arduino2')
