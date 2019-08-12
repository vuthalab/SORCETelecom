import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time


class USBTMC:
    """Simple implementation of a USBTMC device driver, in the style of visa.h"""

    def __init__(self, device):
        self.device = device
        self.file = os.open(device, os.O_RDWR)

        # TODO: Test that the file opened

    def write(self, command):
        os.write(self.file, command)

    def read(self, length=4000):
        return os.read(self.file, length)

    def getName(self):
        self.write("*IDN?")
        return self.read(300)

    def sendReset(self):
        self.write("*RST")


class RigolScope:
    """Class to control a Rigol DS1000 series oscilloscope"""
    def __init__(self, device):
        self.meas = USBTMC(device)

        self.name = self.meas.getName()

        print(self.name)

    def write(self, command):
        """Send an arbitrary command directly to the scope"""
        self.meas.write(command)

    def read(self, command):
        """Read an arbitrary amount of data directly from the scope"""
        return self.meas.read(command)

    def reset(self):
        """Reset the instrument"""
        self.meas.sendReset()
        
    def plot_trace(self,label='',save=False):
        # Initialize our scope
        
        # Stop data acquisition
        self.write(":STOP")
        
        # Grab the data from channel 1
        self.write(":WAV:POIN:MODE NOR")
        
        self.write(":WAV:DATA? CHAN1")
        rawdata = self.read(9000) #number of points to read from the scope
        data = np.frombuffer(rawdata, 'B')
        
        # Get the voltage scale
        self.write(":CHAN1:SCAL?")
        voltscale = float(self.read(20))
        
        # And the voltage offset
        self.write(":CHAN1:OFFS?")
        voltoffset = float(self.read(20))
        
        # Walk through the data, and map it to actual voltages
        # First invert the data
        data = data * -1 + 255
        
        # Now, we know from experimentation that the scope display range is
        # actually 30-229.  So shift by 130 - the voltage offset in counts,
        # then scale to get the actual voltage.
        data = (data - 130.0 - voltoffset/voltscale*25) / 25 * voltscale
        
        # Grab the data from channel 2
        self.write(":WAV:POIN:MODE NOR")
        
        self.write(":WAV:DATA? CHAN2")
        rawdata2 = self.read(9000)
        data2 = np.frombuffer(rawdata2, 'B')
        
        # Get the voltage scale
        self.write(":CHAN2:SCAL?")
        voltscale2 = float(self.read(20))
        
        # And the voltage offset
        self.write(":CHAN2:OFFS?")
        voltoffset2 = float(self.read(20))
        
        # Walk through the data, and map it to actual voltages
        # First invert the data
        data2 = data2 * -1 + 255
        
        # Now, we know from experimentation that the self display range is
        # actually 30-229.  So shift by 130 - the voltage offset in counts,
        # then scale to get the actual voltage.
        data2 = (data2 - 130.0 - voltoffset2/voltscale2*25) / 25 * voltscale2
        
        # Drop the first 10 data points - for some reason, they're always the
        # same.
        data = data[10:]
        data2 = data2[10:]
        
        # Get the timescale
        self.write(":TIM:SCAL?")
        timescale = float(self.read(20))
        
        # Get the timescale offset
        self.write(":TIM:OFFS?")
        timeoffset = float(self.read(20))
        
        # Now, generate a time axis.  The self display range is 0-600, with
        # 300 being time zero.
        time_axis = np.arange(-300.0/50*timescale, 300.0/50*timescale, timescale/50.0)
        
        # If we generated too many points due to overflow, crop the length of
        # time.
        if time_axis.size > data.size:
            time_axis = time_axis[0:data.size]
        
        # See if we should use a different time axis
        if time_axis[-1] < 1e-3:
            time_axis = time_axis * 1e6
            tUnit = "uS"
        elif time_axis[-1] < 1:
            time_axis = time_axis * 1e3
            tUnit = "mS"
        else:
            tUnit = "S"
    
        
        # Start data acquisition again, and put the scope back in local mode
        self.write(":RUN")
        self.write(":KEY:FORC")
        
        header_str = label
        
        # Plot the data
        fig, ax1 = plt.subplots()
        ax1.plot(time_axis, data,label=header_str)
        ax1.set_xlabel("Time (" + tUnit + ")")
        ax1.set_ylabel("Voltage (V) Channel 1 - signal")
        
        ax2 = ax1.twinx()
        ax2.plot(time_axis, data2, color="r")
        ax2.set_ylabel("Voltage (V) Channel 2 - scan")
        
        plt.title("Oscilloscope")
        plt.xlim(time_axis[0], time_axis[-1])
        
        ax1.legend()
        
        fig.tight_layout()
        plt.show()

        if(save==True):
            os.chdir('/home/vuthalab/electric.atoms@gmail.com/data/Rb2Photon')
            now = datetime.fromtimestamp(time.time())
            fname = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+":"+str(now.minute)+":"+str(now.second)
            plt.savefig(fname+'.svg',format='svg')
            plt.savefig(fname+'.png',format='png')
        
        # save raw files in .txt format

    