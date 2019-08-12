import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib import rc
import glob

import sys
import time
from collections import OrderedDict
from digitizer import Digitizer                        # Keysight digitizer
from datetime import datetime
import time


signal_voltage_range = 6 #6# V 
signal_channel = 1 
T_measure = 10e-3 #10e-3# s
sampling_rate = 2e6 #1e5 #2e6#Maximum sampling rate on digitizer  
n_trials = 15
num_samples = T_measure * sampling_rate

dT = 1/sampling_rate
T = num_samples*dT
df = 1.0/T


G_nu = (14e6/520)*(208/3.0)
#G_nu = 4.08e6# * 116408/2122 #7.5e6/(np.sqrt(5)/3) # Hz / V. USER INPUT

file_name = "arduino_sof_v2"

## housekeeping

print(num_samples)
saving_directory = '/home/vuthalab/electric.atoms@gmail.com/Rb2Photon/data/digitizer/'


now = datetime.fromtimestamp(time.time())
time_stamp = str(now.year)+"-"+str(now.month)+"-"+str(now.day)+"-"+str(now.hour)+":"+str(now.minute)+":"+str(now.second)

os.chdir(saving_directory)
new_dir = file_name+"_"+time_stamp
os.mkdir(new_dir)

os.chdir(saving_directory+new_dir)

## Load Digitizer 
DG = Digitizer('/dev/Digitizer', ch1_voltage_range= signal_voltage_range, ch2_voltage_range=4, num_samples=num_samples, sampling_rate=sampling_rate, data_format='float32') # float32 returns voltages directly, no conversion required
DG.status_report()

print ("Digitizer clock status: " + DG.clock_status()) # Make sure that the digitizer is receiving is an external clock. Or change the digitizer.py file to have it run on an internal clock


## Acquire Data
for i in range(n_trials):
    print ('Trial ' + str(i))
    V1 = DG.get_single_channel_waveform(signal_channel)
    
    np.savetxt("data_set" +str(i) + ".txt", V1) 


def test_sine(t):
    return 2*np.sin(2*np.pi*1000*t) + 0.5*np.sin(2*np.pi*3500*t)

def lorentzian(x, b, a, x_0, sigma) :
    # A lorentzian peak with:
    #   Constant Background          : p[0]
    #   Peak height above background : p[1]
    #   Central value                : p[2]
    #   Full Width at Half Maximum   : p[3]
    return b+a/(1.0+((x-x_0)/sigma)**2)




## Load data

data_files = '*.txt'
data_list = glob.glob(data_files)
#data_list = data_list[0]

## FFT
S_nu_list = []
for filename in data_list:
    print ('Processing file ' + filename)
    signal = np.loadtxt(filename, unpack = True)
    signal_ac = signal - np.average(signal)
    freq_noise = G_nu * signal_ac # Converting from voltage noise to frequency noise

    # FFT of signal
    yfft = np.fft.fftshift( np.fft.fft(freq_noise,norm="ortho") ) / np.sqrt(df/dT)  # watch out for this normalization factor
    f = np.fft.fftshift( np.fft.fftfreq(len(freq_noise), dT) )

    # # checking normalization using Parseval's theorem
    # t_sum = np.sum(np.abs(freq_noise)**2 * dT)
    # print "Time integral = ", t_sum
    # f_sum = np.sum(np.abs(yfft)**2 * df)
    # print "Frequency integral = ", f_sum
    # print f_sum/t_sum

    S_nu_trace = np.abs(yfft)**2 /T # Power spectal density of voltage
    S_nu_list.append(S_nu_trace)

S_nu = np.mean(S_nu_list, axis = 0)
W_nu = 2 * S_nu[f>0]
f_plus = f[f>0]

# check parseval again
# print np.sum(S_nu*df) / np.sum(W_nu*df)

## rms frequency, sanity check
delta_nu_rms = np.std(freq_noise)         # time domain rms
alt_nu_rms = np.sqrt( np.sum(W_nu * df) ) # freq domain rms

print (delta_nu_rms)
print (alt_nu_rms)



## phase noise spectrum
f_cut = 2e6                            # ignore frequencies higher than this cutoff
f_integration_stop = 1e6               # only integrate up to this frequency

W_phi = W_nu/f_plus**2

W_phi_reduced = W_phi[f_plus < f_cut]
f = f_plus[f_plus < f_cut]

print('Calculating linewidth . . .')
var_phi = np.zeros(f.shape)

for i in range(len(f[f< f_integration_stop])):
    var_phi[i] = np.trapz(W_phi_reduced[f>f[i]],x=f[f>f[i]])


subt_list = [np.abs(s-(1/np.pi)) for s in var_phi]
linewidth = f_plus[subt_list.index(min(subt_list))]

print('Plotting . . .')
fig = plt.figure(figsize=(11,6))
ax = fig.add_subplot(111)
ax.loglog(f_plus,np.sqrt(W_phi),color='C0',lw=2)
ax.set_ylabel("Phase noise spectral density, $\sqrt{W_\phi(f)}$ [rad/$\sqrt{\mathrm{Hz}}$]",color='C0')
ax.set_xlabel("fourier frequency, $f$")
ax.text(0.7,0.8,'Linewidth = %.2f kHz'%(linewidth*1e-3), transform=ax.transAxes)

ax2 = ax.twinx()
ax2.loglog(f,var_phi,color='C1',lw=2)
ax2.loglog(f_plus,np.ones(f_plus.shape)/np.pi,'k--',lw=2)
ax2.set_ylabel("Phase variance, $\Delta \phi^2 = \int_f^\infty W_\phi(f') \, df'$ [rad$^2$]",color='C1')
ax2.set_ylim(1e-2,1e2)
ax.grid(True)

for fmt in ['png','svg','pdf']:
    fig.savefig("phase_noise." + fmt,format=fmt)

plt.show()

## frequency noise spectrum plot
fig, ax = plt.subplots()
ax.loglog(f_plus, np.sqrt(W_nu))
plt.xlabel('$f$ [Hz]')
plt.ylabel(r'$W_\nu^{1/2}$ [Hz/$\sqrt{\mathrm{Hz}}$]')
plt.grid()

for fmt in ['png','svg','pdf']:
    fig.savefig("frequency_noise." + fmt,format=fmt)

plt.show()