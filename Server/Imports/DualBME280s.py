import board
import busio
import adafruit_bme280
i2c = busio.I2C(board.SCL, board.SDA)
bme280A = adafruit_bme280.Adafruit_BME280_I2C(i2c)
bme280B = adafruit_bme280.Adafruit_BME280_I2C(i2c,address = 0x76)

#print("Temp A is of:", bme280A.temperature)
#print("Humidity A is of:", bme280A.humidity)
#print("Pressure A is of:",bme280A.pressure)

#print("Temp B is of:", bme280B.temperature)
#print("Humidity B is of:", bme280B.humidity)
#print("Pressure B is of:",bme280B.pressure)

def temp():
    return [bme280A.temperature,bme280B.temperature]


def humidity():
    return [bme280A.humidity,bme280B.humidity]

def pressure():
    return [bme280A.pressure,bme280B.pressure]
