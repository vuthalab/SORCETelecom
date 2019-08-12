/* 
 */

#include <EEPROM.h>
#include <analogShield.h>
#include <math.h>
#include<SPI.h>  // for ChipKit uc32 (SPI.h has to be included **after** analogShield.h)

#define UNO_ID "rb_lock\r\n"
#define ZEROV 32768 //Zero volts
#define V2P5 49512  // 2.5 V


//#define OUTPUT_MAX 1.0 //
//#define OUTPUT_MIN -1.0 //

float OUTPUT_MAX = 1.0;
float OUTPUT_MIN = -1.0;

#define RAMP_ON 1
#define RAMP_OFF 0

struct Params {
  int ramp_state;
  float ramp_amplitude;
  float ramp_offset;
  float ramp_frequency;
};

Params params;
Params temp_buffer;

float half_period;
float ramp_slope;

float out0;


float ToVoltage(float bits) {
  return (bits-32768)/6553.6;
}

float ToBits(float voltage) {
  return voltage*6553.6+32768;
}


void setup() {
  //SPI.setClockDivider(SPI_CLOCK_DIV2);
  Serial.begin(115200);
  
  // put your setup code here, to run once:
  
  out0 = 0.0;

  params.ramp_state = 0;
  params.ramp_amplitude = 0.2; //volts
  params.ramp_frequency = 45;
  params.ramp_offset = 0; 

  
  processParams();
  //analog.write(1,ToBits(2.0));
  //analog.write(2,ToBits(3.0));
  //analog.write(3,ToBits(-1.0));
  analog.write(0,ToBits(0.0));
}

float limitOutput(float output) {
  float new_output;
  if(output>OUTPUT_MAX){
    new_output = OUTPUT_MAX;
  }
  else if(output<OUTPUT_MIN) {
    new_output = OUTPUT_MIN;
  }
  else {
    new_output = output;
  }
  return new_output;
}

void processParams() {
  ramp_slope = 4*params.ramp_amplitude*params.ramp_frequency*0.000001; // V/us
  half_period = 1000000/(2*params.ramp_frequency); // us

}

void rampCycle() {
  long ramp_time;
  long start_time;

  /*ramp up */
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    out0 = (ramp_slope*ramp_time - params.ramp_amplitude + params.ramp_offset);
    out0 = limitOutput(out0);
    analog.write(0,ToBits(out0)); 
  }
  /* ramp down */
  start_time = micros();
  ramp_time = 0;
  while(ramp_time<half_period){
    ramp_time = micros() - start_time;
    out0 = (-ramp_slope*ramp_time + params.ramp_amplitude + params.ramp_offset);
    out0 = limitOutput(out0);
    analog.write(0,ToBits(out0)); 
  }
}

void loop() {
    
  if(Serial.available()){
    parseSerial();
  }


  // -----------------------------------------------------------------
  if(params.ramp_state == RAMP_ON) {
    rampCycle();
  }
  
  // -------------------------------------------------------------------
  if(params.ramp_state == RAMP_OFF) {
    
   out0 = limitOutput(params.ramp_offset);
   analog.write(0,ToBits(out0));  //WRITE OUT THE CORRECTION SIGNAL
  }
  
  // -----------------------------------------------------------------
  
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
      Serial.write(UNO_ID); //
      break;
    case 's':
      // set params struct
      Serial.readBytes((char *) &temp_buffer, sizeof(Params));
      if(temp_buffer.ramp_state<=1 && temp_buffer.ramp_state>=0){ //sanity check - make sure nothing went wrong in receiving the data
        params = temp_buffer;
        processParams(); //update the parameters as they've been changed in the python interface
        Serial.println("Success");
      }
      else {
        Serial.println("Inappropriate data fetched");
      }
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
