// Scan the laser, then detect:
//   a) if there is a line
//   b) which line was scanned over

#include <analogShield.h>

// Amplitude, offset in V; period in ms
void scan_and_read(float amplitude, int period, int offset, int num_ramps, int points_per_ramp, unsigned int data[]) {
  period = period * 1e3; // Convert period to μs
  
  int measure_every = period / points_per_ramp;
  unsigned long last_measurement = micros();
  int i = 0;
  
  for (int ramp = 0; ramp < num_ramps; ramp++) {
    while (micros() - period_start < period) {
      float V = (offset - amplitude) + 2 * amplitude * micros() / period;
      analog.write(0, to_bits(V));

      if (micros() > last_measurement + measure_every) {
        data[i] = analog.read(0);
        last_measurement = micros();
        i++;
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
}

void loop() {
  int points_per_ramp = 1000;
  int num_ramps = 16;
  unsigned int data[] = new unsigned int[points_per_ramp * num_ramps];
  scan_and_read(1, 5, 0, num_ramps, points_per_ramp, data);
}
