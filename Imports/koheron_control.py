import time
import numpy as np
import serial

CURR_MAX = 90.0 #mA
CURR_MIN = 65.0 #mA


class KoheronController:
    def __init__(self,portname):
        self.device = serial.Serial(portname,
                                    baudrate=115200,
                                    timeout=0.001)
        self.device.flush()
        
        #self.version = self.ask("version")
        #print("Connected to Koheron controller version %s"%self.version)
        self.ramp = False
        
        time.sleep(0.05)
        
        # the controller has a maximum resistance (min temp) setting
        self.device.write(b'rtmax 25000') # changes max res. to 25000 from 15000
        
        self.device.flush()
        
                
    def write(self,command):
        command = command.encode('utf-8')
        self.device.write(command+b"\r")
    
    def ask(self,command):
        command = command.encode('utf-8')
        self.device.write(command+b"\r")
        time.sleep(0.050)  # this is important !
        response = self.device.readlines()
        return response[1].strip(b'\r\n')
        
    def close(self):
        self.device.close()
        
    def set_temp(self,temp):
        """Set setpoint temperature in deg C"""
        
        res = get_resistance(temp) # in Ohms
        self.write('rtset '+str(res))
        
    def read_set_temp(self):
        """Read setpoint temperature in deg C"""
        res = self.ask('rtset') # in Ohms
        TSET = get_temp(float(res)) # in deg C
        return TSET
        
    def read_temp(self):
        """Read actual temperature in deg C"""
        res = self.ask('rtact') # in Ohms
        TEMP = get_temp(float(res)) # in deg C
        return TEMP
        
    def stream_data(self):
        """Stream actual temperature in deg C and laser current in mA"""
        try:
            while True:
                temp = get_temp(float(self.ask('rtact')))
                curr = float(self.ask('ilaser'))
                volt = float(self.ask('vlaser'))
                if(float(self.ask('lason'))==1):
                    onoff = 'On'
                else:
                    onoff = 'Off'
                print("Temperature: %.3f C   Laser: %s   Current: %.3f mA    Laser voltage: %.3f V"%(temp,onoff,curr,volt))
        except KeyboardInterrupt: pass
    
    def set_current(self,current):
        """Set current in mA """
        self.write('ilaser '+str(current))
    
    def laser_on(self):
        """ Turn Laser on """
        self.write('lason 1')
        
    def laser_off(self):
        """ Turn laser off """
        self.write('lason 0')
    
    def read_current(self):
        """Read laser current in mA"""
        curr = self.ask('ilaser') # in mA
        return curr
        
    def increase_current(self,adjust=0.02):
        """Increase laser current by 0.02 mA """
        curr = float(self.ask('ilaser'))
        if(curr<CURR_MAX and curr>CURR_MIN):
            curr+=adjust
            self.write('ilaser '+str(curr))
        
    def decrease_current(self,adjust=0.02):
        """ Decrease laser current by 0.02 mA """
        curr = float(self.ask('ilaser'))
        if(curr<CURR_MAX and curr>CURR_MIN):
            curr-=adjust
            self.write('ilaser '+str(curr))
    
    # def ramp_current(self,amplitude,n_steps = 80.0, freq = 100.0):
    #     """Ramp laser diode with set amplitude in mA"""
    #     time_delay = 1/(n_steps*freq) #in s
    #     step_size = 2.0*amplitude/n_steps
    #     curr = float(self.ask('ilaser')) #mA
    #     
    #     if(curr<CURR_MAX and curr>CURR_MIN):
    #         self.ramp = True
    #         print("Ramping - use keyboard interrupt to stop ramping")
    #     
    #     while(self.ramp):
    #         try:
    #             new_curr = curr - amplitude/2.0
    #             for i in range(n_steps):
    #                 self.write('ilaser '+str(new_curr))
    #                 new_curr += step_size
    #                 time.sleep(time_delay)
    #             for i in range(n_steps):
    #                 self.write('ilaser '+str(new_curr))
    #                 new_curr -= step_size
    #                 time.sleep(time_delay)
    #         except(KeyboardInterrupt):
    #             self.ramp = False
    #             break

        
## command list

"""
== Control commands ==

    lason: Should be set to 1 to enable the laser current (default value: 0)
    ilaser: Laser current in mA (default value: 0.0).
    rtset: Thermistor resistance setpoint in Ohm (default value: 10000.0).
    pgain: Proportional gain of the temperature controller (default value: 0.001).
    igain: Integral gain of the temperature controller (default value: 0.0001).
    dgain: Differential gain of the temperature controller (default value: 0.005).
    rtmin: Minimum thermistor resistance in Ohm. Below this value, the laser is automatically disabled (default value: 5000.0).
    rtmax: Maximum thermistor resistance in Ohm. Above this value, the laser is automatically disabled (default value: 15000.0).
    vtmin: Minimum TEC voltage in V (default value: -2.0).
    vtmax: Maximum TEC voltage in V (default value: 2.0).

== Status commands ==

    version: Return the firmware version (e.g. V0.1)
    lason: Laser status (0 when disabled, 1 when enabled)
    vlaser: Laser voltage in V.
    iphd: Photodiode current in mA (maximum value: 2.5 mA).
    rtact: Actual value of the thermistor resistance in Ohm.
    itec: TEC current in A.
    vtec: TEC voltage in V.
    ain1: Voltage on pin AIN1 in V.
    ain2: Voltage on pin AIN2 in V.
"""
## Temp stuff
# constants for temperature conversion for Thorlabs 10k thermistors (from https://www.thorlabs.com/_sd.cfm?fileName=4813-S01.pdf&partNumber=TH10K)
a = 3.354017e-3
b = 2.5617244e-4
c = 2.1400943e-6
d = -7.2405219e-8

def get_temp(resistance):
    """Returns temperature in deg C"""
    #Calculates thermistor resistance
    logarith = np.log(resistance/10000.0) #Logarithm required
    T = 1.0/(a + b * logarith + c * (logarith ** 2) + d * (logarith ** 3)) #Temperature calulcation
    return (T - 273.15)


A = -1.5470381e1
B = 5.6022839e3
C = -3.7886070e5
D = 2.4971623e7

def get_resistance(temp):
    """Returns resistance in deg C"""
    tempC = temp + 273.15
    Rth = (10000.0)*np.exp(A + B/tempC + C/(tempC ** 2) + D/(tempC ** 3))
    return Rth #Thermistor resistance

## Control commands

#kc = KoheronController("/dev/ttyUSB4") # use dmesg to find dev port 


    
    
    
    
    
    