#include <EEPROM.h>
#include <Arduino.h>  // for type definitions
#include<SPI.h>
#include <analogShield.h>

#define UNO_ID "DUAL_TEMP_CO_0\r\n"
#define GATE_VOLTAGE_MIN 0.0
#define GATE_VOLTAGE_MAX 1.24
#define N_ACCUM 100

#define ZEROV 32768 //Zero volts

struct Params {
  unsigned int enable0;
  unsigned int set_temp0;
  float prop_gain0;
  float pi_pole0;
  float pd_pole0;

  unsigned int enable1;
  unsigned int set_temp1;
  float prop_gain1;
  float pi_pole1;
  float pd_pole1;
  
};

struct Logger {

  unsigned int gate_voltage0;
  unsigned int gate_voltage1;

  float error_signal0;
  float error_signal1;

  float accumulator0;
  float accumulator1;

  float dt_seconds;
  
};

Params params;
Logger logger;

unsigned long current_time;

float accumulator_small0;
float accumulator_small1;
float prop_term0;
float prop_term1;
float derivative_term0;
float derivative_term1;
float error_signal_instant0;
float error_signal_instant1;

unsigned int n_accum0;
unsigned int n_accum1;

float alpha_avg;

float toVoltage(unsigned int bits) {
  return ((float)(bits-ZEROV))/6553.6; // Convert a number of bits 0<b<65536 to a voltage -5V<V<5V 
}

unsigned int toBits(float voltage) {
  return voltage*6553.6+ZEROV; // Convert a voltage -5V<V<5V to a number of bits 0<b<65536
}

void setup() {
  SPI.setClockDivider(SPI_CLOCK_DIV2);
  /* Open serial communications, initialize output ports: */
  Serial.begin(115200);

  logger.gate_voltage0 = ZEROV;
  logger.gate_voltage1 = ZEROV;

  logger.error_signal0 = 0;
  logger.error_signal1 = 0;

  params.set_temp0 = ZEROV;
  params.set_temp1 = ZEROV;
  
  logger.accumulator0 = 0.0;
  logger.accumulator1 = 0.0;
  
  accumulator_small0 = 0.0;
  accumulator_small1 = 0.0;
  prop_term0 = 0.0;
  prop_term1 = 0.0;
  error_signal_instant0 = 0.0;
  error_signal_instant0 = 0.0;
  n_accum0 = 0;
  
  alpha_avg = 1./N_ACCUM;
  
  analog.write(params.set_temp0, params.set_temp1,
               logger.gate_voltage0,logger.gate_voltage1,
               true);



   EEPROM_readAnything(0, params);
   EEPROM_readAnything(sizeof(params), logger);
   current_time = micros();  
   
}

void loop() {
  unsigned long previous_time = current_time;
  current_time = micros();
  logger.dt_seconds = ((float)(current_time - previous_time))*1e-6;
  
  if(Serial.available())
    parseSerial();

  float error_signal_prev0 = error_signal_instant0;
  float error_signal_prev1 = error_signal_instant1;

  error_signal_instant0 = toVoltage(analog.read(0, true)); //reads the difference between pins 0 and 1
  error_signal_instant1 = toVoltage(analog.read(2, true));

  //logger.error_signal0 = error_signal_instant0*alpha_avg + logger.error_signal0*(1.-alpha_avg);
  //logger.error_signal1 = error_signal_instant1*alpha_avg + logger.error_signal1*(1.-alpha_avg);
  logger.error_signal0 = error_signal_instant0;
  logger.error_signal1 = error_signal_instant1;

  
  if(params.enable0) {
    accumulator_small0 += error_signal_instant0*logger.dt_seconds;
    n_accum0 += 1;
    if(n_accum0 > N_ACCUM) {
      n_accum0 = 0;
      logger.accumulator0 += accumulator_small0*params.prop_gain0*params.pi_pole0;
      accumulator_small0 = 0;
    }

    prop_term0 = 0.99*prop_term0 + 0.01*(error_signal_instant0*params.prop_gain0);

    float der_term = (error_signal_instant0 - error_signal_prev0)/logger.dt_seconds/params.pd_pole0;
    derivative_term0 = 0.995*derivative_term0 + 0.005*(der_term*params.prop_gain0);
    
    float gv0 = logger.accumulator0 + prop_term0;
    
    if (gv0 > GATE_VOLTAGE_MAX) {
      gv0 = GATE_VOLTAGE_MAX;
      logger.accumulator0 = gv0;
    }
    
    if (gv0 < GATE_VOLTAGE_MIN) {
      gv0 = GATE_VOLTAGE_MIN;
      logger.accumulator0 = gv0;
    }
   
    logger.gate_voltage0 = toBits(gv0);
   
  }
  else{
    logger.gate_voltage0 = toBits(GATE_VOLTAGE_MIN);
    logger.accumulator0 = 0.0;
  }

  if(params.enable1) {
    accumulator_small1 += error_signal_instant1*logger.dt_seconds;
    n_accum1 += 1;

    if(n_accum1 > N_ACCUM) {
      n_accum1 = 0;
      logger.accumulator1 += accumulator_small1*params.prop_gain1*params.pi_pole1;
      accumulator_small1 = 0;
    }

    prop_term1 = 0.99*prop_term1 + 0.01*(error_signal_instant1*params.prop_gain1);

    float der_term = (error_signal_instant1 - error_signal_prev1)/logger.dt_seconds/params.pd_pole1;
    derivative_term1 = 0.995*derivative_term1 + 0.005*(der_term*params.prop_gain1);
    
    float gv1 = logger.accumulator1 + prop_term1;

    if (gv1 > GATE_VOLTAGE_MAX) {
      gv1 = GATE_VOLTAGE_MAX;
      logger.accumulator1 = gv1;
    }
    
    if (gv1 < GATE_VOLTAGE_MIN) {
      gv1 = GATE_VOLTAGE_MIN;
      logger.accumulator1 = gv1;
    }
   
    logger.gate_voltage1 = toBits(gv1);
  }
  else{
    logger.gate_voltage1 = toBits(GATE_VOLTAGE_MIN);
    logger.accumulator1 = 0.0;
    
  }
  
  analog.write(params.set_temp0, params.set_temp1,
               logger.gate_voltage0,logger.gate_voltage1,
               true);
//Serial.print(error_signal_instant0,6);
//Serial.print(',');
//Serial.println(params.set_temp0);

}

template <class T> int EEPROM_writeAnything(int ee, const T& value)
{
    const byte* p = (const byte*)(const void*)&value;
    unsigned int i;
    for (i = 0; i < sizeof(value); i++)
          EEPROM.write(ee++, *p++);
    return i;
}

template <class T> int EEPROM_readAnything(int ee, T& value)
{
    byte* p = (byte*)(void*)&value;
    unsigned int i;
    for (i = 0; i < sizeof(value); i++)
          *p++ = EEPROM.read(ee++);
    return i;
}

void parseSerial() {
  char byte_read = Serial.read();
  if(byte_read == 'g') {
    // get params, send the entire struct in one go
    Serial.write((const uint8_t*)&params, sizeof(Params));
  
  }
  if(byte_read == 'l') {
    // send the logger data
    Serial.write((const uint8_t*)&logger, sizeof(Logger));
  
  }
  if(byte_read == 'w') {
    // write to EEPROM
    EEPROM_writeAnything(0, params);
    EEPROM_writeAnything(sizeof(params), logger);
  }
  if(byte_read == 'r') {
    EEPROM_readAnything(0, params);
    EEPROM_readAnything(sizeof(params), logger);
  }
  if(byte_read == 'i') {
    // return ID
    Serial.write(UNO_ID);
  
  }
  if(byte_read == 's') {
    // read in size(Params) bytes
    Params params_temp;
    int bytes_read = Serial.readBytes((char *) &params_temp, sizeof(Params));
    // check for validity of parameters
    params = params_temp;
  } 
}
