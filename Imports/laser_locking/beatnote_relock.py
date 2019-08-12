import time
"""
Determines if L1 and/or L2 are locked to the wrong peak(s) and shifts the current
so that they move to the right peaks. 

Note: Designed to be run inside sorce_control.py, which has object names 
corresponding to the below function parameters.
"""

def beatnote_relock(kc1, kc2, ard1, ard2, fc):
    beatnote_clover_solo = 2.09 # GHz, DESIRED
    beatnote_clover_shaq = 0.57 # GHz
    beatnote_clover_baby = 3.45 # GHz
    beatnote_shaq_solo = 1.52 # GHz
    beatnote_shaq_baby = 2.89 # GHz
    beatnote_solo_baby = 1.37 # GHz
    beatnote_margin = 0.075 # must be less than (1.52 - 1.37) / 2 = 0.08 to allow distinction of peak pairs

    curr_freq_constant_L1 = 2.11 # mA / GHz; negative, but sign ignored for function calls
    # L1 constant measurement: Shaq - 217.600, Clover - 218.800
    curr_freq_constant_L2 = 2.77 # mA / GHz; negative, but sign ignored for function calls
    # L2 constant measurement: Shaq - 220.903,  Clover - 222.483
    
    run = True
    
    while(run):
        time.sleep(0.5)
        fc.get_freq()
        time.sleep(0.5)
        beatnote_frequency = fc.get_freq() * 1e-3
        
        #if abs(beatnote_frequency - beatnote_clover_solo) >= beatnote_margin:
        if abs(beatnote_frequency - beatnote_clover_shaq) >= beatnote_margin:
            print("The lasers are locked to the wrong pair of peaks.")
            print("L1 current: " + str(kc1.read_current()))
            print("L2 current: " + str(kc2.read_current()))
            
            if abs(beatnote_frequency - beatnote_clover_shaq) <= beatnote_margin:
                # move L2 from shaq towards solo (increase L2 frequency)
                kc2.decrease_current(curr_freq_constant_L2 * beatnote_shaq_solo)
                print(1)
            elif abs(beatnote_frequency - beatnote_clover_baby) <= beatnote_margin:
                # move L2 from baby towards solo (decrease L2 frequency)
                kc2.increase_current(curr_freq_constant_L2 * beatnote_solo_baby)
                print(2)
            elif abs(beatnote_frequency - beatnote_shaq_solo) <= beatnote_margin:
                # move L1 from shaq towards clover (decrease L1 in frequency)
                kc1.increase_current(curr_freq_constant_L1 * beatnote_clover_shaq)
                print("L1 current after shift: " + str(kc1.read_current()))
                print(3)
            elif abs(beatnote_frequency - beatnote_shaq_baby) <= beatnote_margin:
                # move L1 from shaq towards clover and move L2 from baby towards solo
                # (decrease both L1 and L2 in frequency)
                kc1.increase_current(curr_freq_constant_L1 * beatnote_clover_shaq)
                kc2.increase_current(curr_freq_constant_L2 * beatnote_solo_baby)
                print(4)
            elif abs(beatnote_frequency - beatnote_solo_baby) <= beatnote_margin:
                # move L1 from solo towards clover and move L2 from baby towards solo
                # (decrease L1 by a lot in frequency and decrease L2 by a little in 
                # frequency)
                kc1.increase_current(curr_freq_constant_L1 * beatnote_clover_solo)
                kc2.increase_current(curr_freq_constant_L2 * beatnote_solo_baby)
                print(5)
            else:
                print("The beatnote frequency is in limbo. Confirm that the lasers are locked.")
                
        run = False
            