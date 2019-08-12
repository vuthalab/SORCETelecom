#include <analogShield.h>
#include <SPI.h>  // for ChipKit uc32 (SPI.h has to be included **after** analogShield.h)

unsigned int counter = 0;

long monitor0;
long monitor1;
long monitor2;
long monitor3;

float to_volts(unsigned int bits) {
  return ((float)bits-32768)/6553.6;
}

void setup() {
  Serial.begin(115200);
}

void loop() {
//  counter ++;
//  long in0 = analog.read(0);
//  analog.write(0,in0);
  
//  if(counter%8000 == 0) {
//    Serial.print(ch0, 6); //error
//    Serial.print(',');
//    Serial.println(ch1, 6); //correction
//  
  monitor0 = analog.read(0,false); //PD Monitor L2
  monitor1 = analog.read(1,false); // PD Monitor L1
  monitor2 = analog.read(2,false); // PMT Monitor L2
  monitor3 = analog.read(3,false); // PMT Monitor L1

  Serial.print(monitor1);
  Serial.print(',');
  Serial.print(monitor0);
  Serial.print(',');
  Serial.print(monitor2);
  Serial.print(',');
  Serial.println(monitor3);
  //}
 delay(100); //ms
  
}
