import os
import time
os.chdir('/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/code/SORCE control')
#os.chdir('/home/pi/electric.atoms@gmail.com/Rb2Photon/code')


import threading
from importlib import reload
#from labjack import ljmreload
#import koheron_control
 
from koheron_control import*
from laser_locking.arduino_peak_lock_v2.arduino_cmd_peak_v2 import*
from cell_temp_control.cell_temp_control_simplified_python import*
from photodiode_monitor import*
from laser_locking.beatnote_relock import*
from minicircuits_frequency_counter import *

# old stuff
#from laser_locking.arduino_lock_v3.arduino_cmd_v3 import*
#from minicircuits_frequency_counter import*
#from arduino_lock_dual_output.arduino_lock_cmd_dual_output import*
#from thorlabs_piezo_driver import*dmesg
#from rigol_scope_control import*
#from laser_locking.arduino_lock_v1.arduino_lock_cmd import*


kc1 = KoheronController("/dev/Koheron1")
kc2 = KoheronController("/dev/Koheron2")
ard1 = ArduinoLocker(serialport='/dev/Arduino1')
ard2 = ArduinoLocker(serialport='/dev/Arduino2')

#ard1 = ArduinoCurrentLocker(serialport='/dev/Arduino1')
#ard2 = ArduinoCurrentLocker(serialport='/dev/Arduino2')

#scope = RigolScope("/dev/usbtmc0")

fc = FrequencyCounter()

pd = PhotodiodeMonitor(serialport='/dev/ArduinoMonitor')

tc = VicorTrimTemperatureController(serialport='/dev/ArduinoCellTemp')


loop_run = False

now = datetime.fromtimestamp(time.time())
time_stamp = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+":"+str(now.minute)+":"+str(now.second)
os.chdir('/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/data/collective data')
filepath = os.path.join(time_stamp+'.txt')


def get_logs():
    global loop_run
    global fp
    while(loop_run):
        now = time.time()
        freq = fc.get_freq()
        err1,err2,corr1,corr2 = pd.get_monitor()
        temp1,temp2 = tc.get_temp()
        print("Freq: %.3f MHz, Err1: %.3f V, Err2:%.3f V, Corr1: %.3f V,Corr2: %.3f V, Temp1: %.3f C, Temp2: %.3f C"%(freq,err1,err2,corr1,corr2,temp1,temp2))
        time.sleep(0.3)
        new_line = str(now)+','+str(freq)+','+str(err1)+','+str(err2)+','+str(corr1)+','+str(corr2)+','+str(temp1)+','+str(temp2)
        fp.write(new_line+'\n')

def start_collection():
    global fp
    fp = open(filepath, 'a+')
    global loop_run
    loop_run = True
    log_thread = threading.Thread(target=get_logs)
    log_thread.start()
    beatnote_relock_thread = threading.Thread(target=beatnote_relock(kc1, kc2, ard1, ard2, fc))
    beatnote_relock_thread.start()

    
def stop_collection():
    global fp
    fp.close()
    global loop_run
    loop_run = False
    

        

##

    

#class labJack:
#    def __init__(self):
#        self.handle = ljm.openS("T7", "USB", "ANY")
    
        
    # def read_curr(self):
    #     IMON = ljm.eReadName(self.handle, curr_monitor_chan)
    #     curr = float(IMON/20.0 *1000) #mA, could also use get_LD_current (see koheron_helpers.py)
    #     #print "Current:   %10.2fmA" % round(float(IMON)/20.0 * 1000, 2)
    #     return curr
    # 
    # def write_curr(self,curr):
    #     IOUT = ljm.eWriteName(self.handle, curr_mod_out_chan, curr/curr_to_vol) #V


#lj= labJack()
#int_channel = 'DAC0'
#lock_channel = 'DAC1'

#ramp = False

# class Locker:
#     def __init__(self):
#         self.ramp = False
#         self.curr = 81.3
#         self.amplitude = 0.0
#         self.n_steps = 1
#         self.ramp_offset = 0.0
#         self.start_curr =  81.3
#         #ljm.eWriteName(lj.handle,lock_channel,0.0)
#         #ljm.eWriteName(lj.handle,int_channel,0.0)
# 
#     def decrease_offset(self,offset=0.02):
#         self.ramp_offset -= offset
#     
#     def increase_offset(self,offset=0.02):
#         self.ramp_offset += offset
# 
#     def unlock(self):
#         #ljm.eWriteName(lj.handle,lock_channel,0.0)
#         #ljm.eWriteName(lj.handle,int_channel,0.0)
#         ar.ramp_on()
#         
#     
#     def lock(self):
#         ar.ramp_off()
#         #ljm.eWriteName(lj.handle,lock_channel,5.0)
#         #ljm.eWriteName(lj.handle,int_channel,5.0)

    # def ramp_on(self,amplitude=0.05,n_steps = 20):
    #     """Ramp laser diode with set amplitude in mA, freq in Hz"""
    #     self.amplitude = amplitude
    #     self.n_steps = n_steps
    #     ljm.eWriteName(lj.handle,lock_channel,0.0)

    #     lj_voltage = 0.0
    #     ljm.eWriteName(lj.handle, ramp_channel, lj_voltage) #V
    #     
    #     self.start_curr = self.curr 
    #     
    #     self.ramp = True
    #     print("Ramping")
    #     ramp_thread = threading.Thread(target=self.ramp_current)
    #     ramp_thread.start()
    # 
    # def ramp_off(self):
    #     self.ramp = False
    #     self.curr = self.start_curr+self.ramp_offset
    #     kc.set_current(self.curr)
    #     self.ramp_offset = 0.0
    #     print("Ramp off")
    
    
    # def ramp_current(self):

    #       step_size = 2.0*self.amplitude/self.n_steps
    #     lj_voltage = 0.0
    #     loop_counter = 0
    #     while(self.ramp):
    #         loop_counter +=1
    #         if(loop_counter%20==0):
    #             print(kc.read_current())
    #         try:
    #             try:
    #                 curr = self.start_curr + self.ramp_offset
    #             except:
    #                 pass
    #             if(curr<CURR_MAX and curr>CURR_MIN):
    #                 new_curr = curr - self.amplitude
    #             else:
    #                 print("error - garbage read")
    #                 break

   ##               for i in range(self.n_steps):
    #                 kc.set_current(new_curr)
    #                 ljm.eWriteName(lj.handle, ramp_channel, lj_voltage) #V
    #                 time.sleep(0.050)  # this is important !
    #                 new_curr += step_size
    #                 lj_voltage+= 2.0*step_size
    #                 #print(kc.ask('ilaser'))
    #     
    #             for i in range(self.n_steps):
    #                 kc.set_current(new_curr)
    #                 ljm.eWriteName(lj.handle, ramp_channel, lj_voltage) #V
    #                 time.sleep(0.050)  # this is important !
    #                 new_curr -= step_size
    #                 lj_voltage -= 2.0*step_size
    #                 #print(kc.ask('ilaser'))
    #         except(KeyboardInterrupt):
    #             self.ramp = False
    #             break

    # def lock(self):
    #     self.ramp_off()
    #     ljm.eWriteName(lj.handle,lock_channel,2.0)
    #     
    # def unlock(self):
    #     ljm.eWriteName(lj.handle,lock_channel,0.0)
    #     self.ramp_on()

        

#locker = Locker()
