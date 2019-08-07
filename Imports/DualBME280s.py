import board
import busio
import adafruit_bme280
i2c = busio.I2C(board.SCL, board.SDA)

### Conecting to both BME280 sensors
try:
    bme280A = adafruit_bme280.Adafruit_BME280_I2C(i2c)
except:
    print("Could not connect to BME280A")
try:
    bme280B = adafruit_bme280.Adafruit_BME280_I2C(i2c,address = 0x76)
except:
    print("Could not connect to BME280B")

#print("Temp A is of:", bme280A.temperature)
#print("Humidity A is of:", bme280A.humidity)
#print("Pressure A is of:",bme280A.pressure)

#print("Temp B is of:", bme280B.temperature)
#print("Humidity B is of:", bme280B.humidity)
#print("Pressure B is of:",bme280B.pressure)

# Function to try to get the temperature readings of the sensors
def temp():
    temp = [999,999]
    try:
        temp[0] = bme280A.temperature
    except:
        temp[0] = 999
    try:
        temp[1] = bme280B.temperature
    except:
        temp[1] = 999

    return temp

# Function to try to get the humidity readings of the sensors 
def humidity():
    Humid = [-1,-1]
    try:
        Humid[0] = bme280A.humidity
    except:
        Humid[0] = -1
    try:
        Humid[1] = bme280B.humidity
    except:
        Humid[1] = -1

    return Humid

# Function to try to get the pressure readings of the sensors
def pressure():
    pressure = [-1,-1]
    try:
        pressure[0] = bme280A.pressure
    except:
        pressure[0] = -1
    try:
        pressure[1] = bme280B.pressure
    except:
        pressure[1] = -1

    return pressure