import time
import numpy as np
import serial
import re

class PiezoDriver:
    def __init__(self,portname):
        self.device = serial.Serial(portname,baudrate=115200,timeout=0.001)
        self.device.flush()
        time.sleep(0.05)
        self.device.flush()
        
                
    def write(self,command):
        command = command.encode('utf-8')
        self.device.write(command+b"\r")
        
    def set_output_voltage(self,voltage):
        self.write('XV'+str(voltage))
    
    def read_output_voltage(self):
        self.write('XR?')
        time.sleep(0.050)  # this is important !
        response = self.device.readlines()
        output_voltage = float(re.findall("\d+\.\d+", str(response[0]))[0])
        return output_voltage
        
    def increase_voltage(self,adjust=0.2):
        curr_vol = self.read_output_voltage()
        new_vol = curr_vol+adjust
        self.set_output_voltage(new_vol)
        
    def decrease_voltage(self,adjust=0.2):
        curr_vol = self.read_output_voltage()
        new_vol = curr_vol-adjust
        self.set_output_voltage(new_vol)