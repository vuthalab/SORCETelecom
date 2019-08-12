#include <EEPROM.h>
#include <analogShield.h>
#include <math.h>
#include <SPI.h>  // for ChipKit uc32 (SPI.h has to be included **after** analogShield.h)

#define ZEROV 32768 //Zero volts
#define V5 65535 // 5 V

#define IN_CHAN 0
#define OUT_CHAN 0

#define PMT_OUT_CHAN 1

#define STATE_LOCKING 0
#define STATE_SCANNING 1

//#define ACCUMULATOR2_MAX 2000 //when accumulator is greater than this may be out of lock - code will auto relock
#define AUTO_RELOCK_TRIGGER 32768 //-0 V

#define OUT_MAX 52429 //3V
#define OUT_MIN 13107 //-3V

#define PMT_OUT_MAX 39322 // 1V
#define PMT_OUT_MIN 36045 // 0.5V

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

Params params;
Params temp_buffer;

long sig_peak_in;
long sig_peak_out;
long sig_half_peak;
long lock_start_point = ZEROV;

float half_period;
float ramp_slope;

float error_signal = 0.0;
float accumulator = 0.0;
float accumulator2 = 0.0;

int get_sampling_rate = 0;
long start_time = 0;
long sampling_time = 0;

//float hwhm_jump = 0;
long jump_voltage_bits = 0;
float corr_out = 0;

/*---------------FUNCTIONS-----------------------*/

float ToVoltage(float bits) {
  return (bits-32768)/6553.6;
}

float ToBits(float voltage) {
  return voltage*6553.6+32768;
}

long limitOutput(long output) {
  long new_output;
  if(output>OUT_MAX){new_output = OUT_MAX;}
  else if(output<OUT_MIN) {new_output = OUT_MIN;}
  else {new_output = output;}
  return new_output;
}

long limitPmtOutput(long output) {
  long new_output;
  if(output>PMT_OUT_MAX){new_output = PMT_OUT_MAX;}
  else if(output<PMT_OUT_MIN) {new_output = PMT_OUT_MIN;}
  else {new_output = output;}
  return new_output;
}

void processParams() {
  ramp_slope = 4*params.ramp_amplitude*params.ramp_frequency*0.000001; // V/us
  half_period = 1000000/(2*params.ramp_frequency); // us
  jump_voltage_bits = ToBits(params.jump_voltage)-ZEROV;
  analog.write(PMT_OUT_CHAN,limitPmtOutput(ToBits(params.pmt_gain_voltage)));
  // Things to do when you hit "lock":
  if(params.scan_state==STATE_LOCKING){
    accumulator = 0.0;
    accumulator2=0.0;
    error_signal = 0.0;
    lock_start_point = sig_peak_out;
    corr_out = sig_peak_out + jump_voltage_bits/2;
    analog.write(OUT_CHAN,limitOutput(sig_peak_out + jump_voltage_bits/2));
    //rampCycle();
    //Serial.println(sig_peak_in);
    //Serial.println(sig_half_peak); //this also happens on auto-relock - how will we catch this?

  }
}

void rampCycle(){
  long ramp_time;
  long start_time;
  float sig_out;
  float sig_in;
  long min_sig_in = V5;
  long min_sig_out; 
    
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    sig_out = ToBits(ramp_slope*ramp_time - params.ramp_amplitude + params.output_offset);
    analog.write(OUT_CHAN,limitOutput(sig_out)); 
    
    sig_in = analog.read(IN_CHAN,false);
    if(sig_in<min_sig_in){
        min_sig_in = sig_in;
        min_sig_out = sig_out;
      }
  }
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    sig_out = ToBits(-ramp_slope*ramp_time + params.ramp_amplitude + params.output_offset);
    analog.write(OUT_CHAN,limitOutput(sig_out)); 

  }
  sig_peak_in = min_sig_in;
  sig_peak_out = min_sig_out;


}





void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  analog.write(ZEROV,ZEROV,ZEROV,ZEROV,true);
  params.scan_state = STATE_SCANNING;
  params.ramp_amplitude = 1.0; //volts
  params.ramp_frequency = 50.0;
  params.output_offset = 0.0;
  params.p_gain = 0.0;
  params.i_gain = 0.0;
  params.i2_gain = 0.0;
  params.alpha = 0.05;
  params.pmt_gain_voltage = 0.5;
  processParams();
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()){
    parseSerial();
  }
  if(get_sampling_rate==1){
    start_time = micros();
  }
  // -----------------------------------------------------------------
  if(params.scan_state == STATE_SCANNING) {
    rampCycle();
  }
  
  // -----------------------------------------------------------------

  if(params.scan_state == STATE_LOCKING) {

    
    long sig_in_lower;
    long sig_in_upper;
    float sig_out;
    sig_in_upper = analog.read(IN_CHAN,false);
    
    analog.write(OUT_CHAN, limitOutput(corr_out - jump_voltage_bits)); 
    sig_in_lower = analog.read(IN_CHAN,false);

    // AUTO RELOCK:
    if(sig_in_lower>AUTO_RELOCK_TRIGGER){
      rampCycle();
      processParams();
    }
    
    float err_curr = ((float)(sig_in_upper- sig_in_lower)); 
    error_signal = (1-params.alpha)*error_signal + params.alpha*err_curr; //low-passed error signal, in bits
    
    
    sig_out = lock_start_point;

    accumulator += params.i_gain*error_signal; //add the integral gain term to the accumulator
    accumulator2 += params.i2_gain*accumulator; //add the integral squared term to the accumualator2

    sig_out += params.p_gain*error_signal+accumulator2+accumulator; // note the overall sign on the gain!
    corr_out = sig_out;
    analog.write(OUT_CHAN,limitOutput(sig_out+jump_voltage_bits/2));  //WRITE OUT THE CORRECTION SIGNAL
//
//    //Check if maxed out:
//    if(corr_out>OUT_MAX){
//      Serial.println("max");
//    }
//    if(corr_out<OUT_MIN){
//      Serial.println("min");
//    }
//
//    //test:
//    Serial.println("testing");

  }

  if(get_sampling_rate==1){
    sampling_time = micros() - start_time;
    Serial.println(sampling_time);
    get_sampling_rate=0;
   }
}


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
    case 's':
      // set params struct
      Serial.readBytes((char *) &temp_buffer, sizeof(Params));
      if(temp_buffer.scan_state<=1 && temp_buffer.scan_state>=0){ //sanity check - make sure nothing went wrong in receiving the data
        params = temp_buffer;
        Serial.println("Success");
        processParams(); //update the parameters as they've been changed in the python interface
        if(params.scan_state==STATE_LOCKING){
          //Serial.println(sig_peak_in);

        }
      }
      else {
        Serial.println("Inappropriate data fetched from python");
      }
      break;
    case 't':
      get_sampling_rate = 1;
      break;
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
