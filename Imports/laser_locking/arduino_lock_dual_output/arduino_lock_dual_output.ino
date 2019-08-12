/* Code written by Shreyas Fall 2017
 *  Modified by Shira Summer 2018
 *  Further Modified for single output by Shira Fall 2018
 *  
 *  Code operates in scanning mode/locking mode
 *  Scanning: sends out a ramp to the current of user-specified amplitude
 *  Locking: uses the centre-of-scan input voltage as a lockpoint, calculate PI^2 correction signal to current modulation
 *  
 *  In0 = photodiode signal
 *  Out0 = current modulation
 *  
 *  Communicates via serial - use with python cmd line program to update parameters and log data
 */

#include <EEPROM.h>
#include <analogShield.h>
#include <math.h>
#include <SPI.h>  // for ChipKit uc32 (SPI.h has to be included **after** analogShield.h)

#define UNO_ID "rb_lock\r\n"
#define ZEROV 32768 //Zero volts
#define V2P5 49512  // 2.5 V
#define V5 65535 // 5.0 V

#define PIEZO_CHAN 0
#define CURRENT_CHAN 1
#define SWITCH_CHAN 2

#define STATE_LOCKING 0
#define STATE_SCANNING 1

#define SIDE_OF_FRINGE 0
#define PEAK 1

#define ACCUMULATOR2_MAX 2000 //when accumulator is greater than this may be out of lock - code will auto relock

#define CURRENT_MAX 39322 //1V
#define CURRENT_MIN 26214 //-1V

#define PIEZO_MAX 65535 //5V
#define PIEZO_MIN 32768 //0V

struct Params {
  float ramp_amplitude; //[0] 
  float current_p_gain, current_i_gain; //[1] [2]
  float piezo_p_gain, piezo_i_gain, piezo_i2_gain; //[3] [4] [5] 
  long output_offset; //[6]
  long scan_state; //[7]
  float ramp_frequency; //[8]
  long sig_peak_voltage; //[9]
  float alpha; //[10]
  long sig_half_max_voltage; //[11]
  long lock_type; // [12]
};

Params params;

Params temp_buffer;

long in0;
long out_piezo;
long out_current;

long ramp_peak_voltage;
long ramp_half_max_voltage;

long sig_half_max_voltage;

long fwhm = 0;
long hwhm = 0;

long peak_trip_voltage;

int max_find_trip = 0;

float half_period;
float ramp_slope;

float error_signal;
float accumulator;
float accumulator2;
float accumulator_current;
long fwhm_bits;

int get_sampling_rate = 0;
long start_time = 0;
long sampling_time = 0;

float err_curr;

float ToVoltage(float bits) {
  return (bits-32768)/6553.6;
}

float ToBits(float voltage) {
  return voltage*6553.6+32768;
}


void setup() {
  //SPI.setClockDivider(SPI_CLOCK_DIV2);
  Serial.begin(115200);
  analog.write(ZEROV,ZEROV,ZEROV,ZEROV,true);
  // put your setup code here, to run once:
  in0 = ZEROV;
  
  out_piezo = ZEROV;
  out_current = ZEROV;

  params.ramp_amplitude = 1.0; //volts

  accumulator = 0.0; //will pause accumulation if gets too big (sudden jump to laser, such as bang on optics table)
  accumulator2 = 0.0; //will not pause, used for i^2 gain
  accumulator_current = 0.0;
  
  params.scan_state = STATE_SCANNING; //code is in scan mode / lock mode
  params.ramp_frequency = 20; // Hz

  ramp_peak_voltage = ZEROV;
  ramp_half_max_voltage = ZEROV;

  params.lock_type = SIDE_OF_FRINGE;
  
  processParams();
  error_signal = ZEROV;//0.0;
}

long limitOutput_piezo(long output) {
  long new_output;
  if(output>PIEZO_MAX){
    new_output = PIEZO_MAX;
  }
  else if(output<PIEZO_MIN) {
    new_output = PIEZO_MIN;
  }
  else {
    new_output = output;
  }
  return new_output;
}

long limitOutput_current(long output) {
  long new_output;
  if(output>CURRENT_MAX){
    new_output = CURRENT_MAX;
  }
  else if(output<CURRENT_MIN) {
    new_output = CURRENT_MIN;
  }
  else {
    new_output = output;
  }
  return new_output;
}

void processParams() {
  ramp_slope = 4*params.ramp_amplitude*params.ramp_frequency*0.000001; // V/us
  half_period = 1000000/(2*params.ramp_frequency); // us
  //accumulator = 0.0;
  //accumulator2=0.0;
  // Things to do when you hit "lock":
  if(params.scan_state==STATE_LOCKING){
    accumulator = 0.0;
    accumulator2=0.0;
    accumulator_current = 0.0;
    rampCycle(true,false); //find the max
    rampCycle(true,true); //find the half max and start locking
    //peak_trip_voltage = 8*params.sig_peak_voltage/10;
    //analog.write(SWITCH_CHAN,ZEROV); //turn switch on
  }
  if(params.scan_state==STATE_SCANNING){
    analog.write(SWITCH_CHAN,V5); //turn switch off
  }
}
void rampCycle(bool find_lock_point, bool start_lock) {
  long ramp_time;
  long start_time;
  float offset = ToVoltage(params.output_offset);

  long sig_in;

  long max_sig_in = ZEROV; 
  
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    out_piezo = ToBits(ramp_slope*ramp_time - params.ramp_amplitude + offset);
    analog.write(PIEZO_CHAN,limitOutput_piezo(out_piezo)); 
    
    if(find_lock_point){
      sig_in = analog.read(0,false);
   
      if(start_lock==false and sig_in<max_sig_in){
        max_sig_in = sig_in;
        ramp_peak_voltage = out_piezo;
      }

      if(start_lock==true and sig_in<sig_half_max_voltage){
        ramp_half_max_voltage = out_piezo;
        hwhm = ramp_peak_voltage - ramp_half_max_voltage;
        fwhm = hwhm*2;
        params.scan_state = STATE_LOCKING;
        break;
      }
    }
  }
  if(find_lock_point){
    sig_half_max_voltage = max_sig_in/2;
  }
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    out_piezo = ToBits(-ramp_slope*ramp_time + params.ramp_amplitude + offset);
    analog.write(PIEZO_CHAN,limitOutput_piezo(out_piezo)); 
  }

}

void loop() {

    
  if(Serial.available()){
    parseSerial();
  }
  if(get_sampling_rate==1){
    start_time = micros();
  }

  // -----------------------------------------------------------------
  if(params.scan_state == STATE_SCANNING) {
    rampCycle(false,false);
  }
  
  // -------------------------------------------------------------------
  if(params.scan_state == STATE_LOCKING) {
    /*
    in0 = analog.read(0, false); //read the voltage on channel 0

    float err_curr = ((float)(in0 - params.lock_point)); //current signal reading, in ??... in0 and lock_point are both in Bits
    error_signal = 0.95*error_signal + 0.05*err_curr; //low-passed error signal, in V
    */
    
    if(params.lock_type==SIDE_OF_FRINGE) {
      in0=analog.read(0,false);
      //err_curr = ((float)(in0-params.sig_half_max_voltage));
      err_curr = ((float)(in0-sig_half_max_voltage));
    }
    
    else{
      long left_sig = analog.read(0,false);
      analog.write(0,out_piezo+fwhm);
      long right_sig = analog.read(0,false);
      err_curr = left_sig - right_sig;
    }
    
    error_signal = (1-params.alpha)*error_signal + params.alpha*err_curr; //low-passed error signal, in V
    
    
    out_piezo = ramp_peak_voltage; //add voltage offset to piezo
    out_current = ZEROV;
  
    accumulator += params.piezo_i_gain*error_signal; //add the integral gain term to the accumulator
    accumulator2 += params.piezo_i2_gain*accumulator; //add the integral squared term to the accumualator2
    accumulator_current += params.current_i_gain*error_signal;

    //AUTO RELOCK:
    if(abs(accumulator2) > ACCUMULATOR2_MAX) { //if accumulator 2 gets too big, out of lock
      // this could mean that we are out of lock... reset  
      processParams();
    }
  
   out_piezo += params.piezo_p_gain*error_signal+accumulator2+accumulator; // note the overall sign on the gain
   out_current -=  params.current_p_gain*error_signal+accumulator_current; 

   if(params.lock_type==SIDE_OF_FRINGE) {
    analog.write(limitOutput_piezo(out_piezo),limitOutput_current(out_current),true);  //WRITE OUT THE CORRECTION SIGNAL
   }

   else{
   analog.write(limitOutput_piezo(out_piezo-hwhm),limitOutput_current(out_current),true);  //WRITE OUT THE CORRECTION SIGNAL
   }
  }
  
  // -----------------------------------------------------------------
  
  /* Output voltages are the following: 
   *  out0 = V_Poff - accumulator 2 - accumulator1 - Pp*error     offset, proportional gain, integral gain, integral^2 gain
   *  
   *  accumulator1: accumulate I*error
   *  accumulator2: accumulate I2*accumulator1
   */
   if(get_sampling_rate==1){
    sampling_time = micros() - start_time;
    Serial.println(sampling_time);
    get_sampling_rate=0;
   }
}

/*
 * g - get params
 * w - write to eeprom
 * r - read from eeprom
 * i - return UNO_ID
 * s - set params
 */
void parseSerial() { //function to read and interpret characters passed from the python interface to the serial port
  char byte_read = Serial.read();

  switch(byte_read) {
    case 'g':
      // get params, send the entire struct in one go
      Serial.write((const uint8_t*)&params, sizeof(Params));
      break;
    case 'w':
      // write to EEPROM // save new default values
      EEPROM_writeAnything(0, params);
      break;
    case 'r':
      EEPROM_readAnything(0, params); //reset to default values
      // EEPROM_readAnything(sizeof(params), logger);      
      break;
    case 'i':
      // return ID
      Serial.write(UNO_ID); //not sure..........
      break;
    case 's':
      // set params struct
      Serial.readBytes((char *) &temp_buffer, sizeof(Params));
      if(temp_buffer.scan_state<=1 && temp_buffer.scan_state>=0){ //sanity check - make sure nothing went wrong in receiving the data
        params = temp_buffer;
        processParams(); //update the parameters as they've been changed in the python interface
        Serial.println("Success");
      }
      else {
        Serial.println("Inappropriate data fetched");
      }
      break;
    case 't':
      get_sampling_rate = 1;
  }
}

template <class T> long EEPROM_writeAnything(long ee, const T& value)
{
    const byte* p = (const byte*)(const void*)&value;
    unsigned int i;
    for (i = 0; i < sizeof(value); i++)
          EEPROM.write(ee++, *p++);
    return i;
}

template <class T> long EEPROM_readAnything(long ee, T& value)
{
    byte* p = (byte*)(void*)&value;
    unsigned int i;
    for (i = 0; i < sizeof(value); i++)
          *p++ = EEPROM.read(ee++);
    return i;
}
