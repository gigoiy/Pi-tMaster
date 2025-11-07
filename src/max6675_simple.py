# max6675_simple.py
import spidev
import time
import RPi.GPIO as GPIO

class MAX6675:
    def __init__(self, cs_pin):
        self.cs_pin = cs_pin
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 500000  # Try slower speed
        self.spi.mode = 0b00  # Explicitly set SPI Mode 0
        self.spi.lsbfirst = False  # MSB first
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)
    
    def read_temp_c(self):
        GPIO.output(self.cs_pin, GPIO.LOW)
        time.sleep(0.001)
        
        data = self.spi.readbytes(2)
        GPIO.output(self.cs_pin, GPIO.HIGH)
        
        if len(data) < 2:
            raise ValueError("Invalid data")
        
        value = (data[0] << 8) | data[1]
        
        if value & 0x04:
            raise ValueError("Thermocouple error")
        
        temp = (value >> 3) & 0xFFF
        return temp * 0.25