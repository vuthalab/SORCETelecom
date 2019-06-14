# Python interface for the Minicircuits UFC-6000 frequency counter
# 2019-05-06, version 1
# Ryan Zazo & Amar Vutha
# https://github.com/vuthalab/UFC-6000-Frequency-Counter

import os
import time

#Frequency Counter Class meant to operate the Mini-Circuits RF Frequency Counter UFC-6000
class FrequencyCounter:
    def __init__(self,address="/dev/FREQCOUNT"):
        """Initializes the Frequency Counter Class, takes an adress as input and prints out a confirmation message"""
        self.fc = os.open(address, os.O_RDWR|os.O_NONBLOCK)        
        print("Connected to:",self.get_model_name(), "with serial number",self.get_serial_number())
        
        
    def get_model_name(self):
        """ Returns the model name of the device, expected return: UFC-6000 """
        os.write(self.fc,b'(\r')
        time.sleep(1)
        return os.read(self.fc,64).decode('UTF-8').split("\x00")[0][1:]
        
        
    def get_serial_number(self):
        """ Returns the serial number of the device, expected return: 11812200037 """
        os.write(self.fc,b')\r')
        time.sleep(1)
        return os.read(self.fc,64).decode('UTF-8').split("\x00")[0][1:]
    
    def get_frequency_and_range(self):
        """ Returns a tuple containing the operating range (1 to 4) and the frequency (MHz) """
        os.write(self.fc,b'\x02\r')
        time.sleep(0.1)
        returned_string = os.read(self.fc,64).decode('UTF-8').split("\x00")[0][1:].strip().split()
        range = returned_string[1]
        frequency = returned_string[2]   # MHz
        return range, frequency

    def set_range(self,range_value):
        """ Set the range of the device, from 1 to 4; 1 is from 1 to 40 MHz, 2 40-190, 3 190-1400 and 4 1400-6000 """
        os.write(self.fc,b'\x04' + bytes([range_value]) + b'\r')
        time.sleep(5)
        os.read(self.fc,64).decode('UTF-8').split("\x00")[0][1:]
        return None
    
    def set_sample_time(self,sample_time):
        """ Sample time of the device in units of 100 ms """
        if (sample_time < 1) or (sample_time > 30): sample_time = 1
        os.write(self.fc,b'\x03' + bytes([sample_time]) + b'\r')
        time.sleep(1)
        os.read(self.fc,64).decode('UTF-8').split("\x00")[0][1:]
        return None
        
    def get_sample_time(self):
        """ Returns the sample time of the device """
        os.write(self.fc,b'!\r')
        time.sleep(1)
        rval = os.read(self.fc,64).decode('UTF-8').split("\x00")[0]
        val = rval.encode(encoding='UTF-8') #Encode the value again to "fix" the return value as to add a binary "b" to it.
        return val[1]
    
frequency_counter = FrequencyCounter()
