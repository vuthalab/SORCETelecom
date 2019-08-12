#include <EEPROM.h>
#include <analogShield.h>
#include <math.h>

#define ZEROV 32768 //Zero volts
#define V5 65535 // 5 V
#define V2P5 49512

#define OUTPUT_MAX 1.30 //V
#define OUTPUT_MIN 0.15 //V
//1.23 V = 15 V on DC-DC convertor

struct Params {
  long enable;
  long set_temp;
  float p_gain;
  float i_gain;
  float i_rolloff; // Damp out old terms in the integrator
  float d_gain;
  float output;
};

struct Logger {
  long temp_0;
  long temp_1;
};

Params params0;
Params params1;
Logger logger;

float alpha = 0.1;

long sig_in0;
long sig_in1;

float curr_err0;
float curr_err1;

float err0 = 0;
float err1 = 0;

float accumulator0 = 0;
float accumulator1 = 0;

unsigned long now, then = 0; // Keeping track of time for derivative calculation

float ToVoltage(float bits) {
  return (bits - 32768) / 6553.6;
}

float ToBits(float voltage) {
  return voltage * 6553.6 + 32768;
}

float limitOutput(float output) {
  if (output < OUTPUT_MIN) {
    return OUTPUT_MIN;
  }
  else if (output > OUTPUT_MAX) {
    return OUTPUT_MAX;
  }
  else {
    return output;
  }
}

void setup() {
  /* Open serial communications, initialize output ports: */
  Serial.begin(115200);

  params0.enable = 0;
  params1.enable = 0;
  params0.set_temp = V2P5;
  params1.set_temp = V2P5;
  params0.p_gain = 10;
  params1.p_gain = 10;
  params0.i_gain = 0;
  params1.i_gain = 0;
  params0.i_rolloff = 0.99;
  params1.i_rolloff = 0.99;
  params0.d_gain = 0;
  params1.d_gain = 0;
  params0.output = 0.96;
  params1.output = 0.96;

  analog.write(0, 1, 2, 3, ToBits(0.96));
  analog.write(3, ToBits(0.96));
}

void loop() {
  if (Serial.available()) {
    parseSerial();
  }

  sig_in0 = analog.read(1, false);//0, false);
  sig_in1 = analog.read(0, false);//1, false);

  then = now;
  while (millis() == then); // Delay until at least 1 millisecond has passed
  now = millis();
  unsigned long dt = now - then;

  logger.temp_0 = sig_in0; // bits
  logger.temp_1 = sig_in1;

  float last_err0 = curr_err0;
  float last_err1 = curr_err1;
  curr_err0 = ToVoltage(params0.set_temp) - ToVoltage(sig_in0);
  curr_err1 = ToVoltage(params1.set_temp) - ToVoltage(sig_in1);

  float off0 = abs(curr_err0 / params0.set_temp);
  float off1 = abs(curr_err1 / params1.set_temp);

  if (params0.enable == 1) {// && off0 < 0.1 * ToVoltage(params0.set_temp)) {
    //lock servo 0 here
    float out0 = params0.output;
    err0 = (1 - alpha) * err0 + alpha * curr_err0; //low pass filtering

    accumulator0 = params0.i_rolloff * accumulator0 + err0 * dt;
    float derivative0 = (curr_err0 - last_err0) / dt;
    
    out0 += params0.p_gain * err0 + params0.i_gain * accumulator0 + params0.d_gain * derivative0;

    params0.output = limitOutput(out0);
    analog.write(0, ToBits(limitOutput(out0)));
  }
  else if (params0.enable == 0) {
    analog.write(0, ToBits(params0.output));
  }

  if (params1.enable == 1) {
    //lock servo1 here
    float out1 = params1.output;
    err1 = (1 - alpha) * err1 + alpha * curr_err1; //low pass filtering

    accumulator1 = params1.i_rolloff * accumulator0 + err1 * dt;
    float derivative1 = (curr_err0 - last_err0) / dt;
    
    out1 += params1.p_gain * err1 + params1.i_gain * accumulator1 + params1.d_gain * derivative1;

    params1.output = limitOutput(out1);
    analog.write(1, ToBits(limitOutput(out1)));
  }
  else if (params1.enable == 0) {
    analog.write(1, ToBits(limitOutput(params1.output)));
  }

  analog.write(2, sig_in1);
}

void parseSerial() {
  char byte_read = Serial.read();
  if (byte_read == 'g') {
    // get params, send the entire struct in one go
    Serial.write((const uint8_t*)&params0, sizeof(Params));
    Serial.write((const uint8_t*)&params1, sizeof(Params));


  }
  if (byte_read == 'l') {
    // send the logger data
    Serial.write((const uint8_t*)&logger, sizeof(Logger));

  }
  //  if(byte_read == 'w') {
  //    // write to EEPROM
  //    EEPROM_writeAnything(0, params0);
  //    EEPROM_writeAnything(sizeof(params0), logger);
  //  }
  //  if(byte_read == 'r') {
  //    EEPROM_readAnything(0, params0);
  //    EEPROM_readAnything(sizeof(params0), logger);
  //  }
  if (byte_read == 's') {
    // read in size(Params) bytes
    Params params_temp;
    int bytes_read = Serial.readBytes((char *) &params_temp, sizeof(Params));
    // check for validity of parameters
    params0 = params_temp;
    int bytes_read2 = Serial.readBytes((char *) &params_temp, sizeof(Params));
    // check for validity of parameters
    params1 = params_temp;
  }
}
