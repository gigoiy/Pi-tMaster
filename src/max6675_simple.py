# max6675_simple.py
import spidev
import time
import RPi.GPIO as GPIO
from calibration import CalibrationManager

class MAX6675:
    def __init__(self, cs_pin, sensor_name="unknown"):
        self.cs_pin = cs_pin
        self.sensor_name = sensor_name
        self.calibration_manager = CalibrationManager()
        
        # Initialize SPI for real hardware
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 500000
        self.spi.mode = 0b00
        self.spi.lsbfirst = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.output(self.cs_pin, GPIO.HIGH)
        
        print(f"Initialized MAX6675 sensor '{sensor_name}' on CS pin {cs_pin}")
    
    def read_temp_c(self):
        """Read temperature from actual MAX6675 hardware"""
        return self._read_actual_temp()
    
    def _read_actual_temp(self):
        """Read actual temperature from MAX6675 sensor"""
        GPIO.output(self.cs_pin, GPIO.LOW)
        time.sleep(0.001)  # Wait for conversion
        
        try:
            data = self.spi.readbytes(2)
            GPIO.output(self.cs_pin, GPIO.HIGH)
            
            if len(data) < 2:
                raise ValueError("Invalid data - less than 2 bytes received")
            
            value = (data[0] << 8) | data[1]
            
            # Check for thermocouple error
            if value & 0x04:
                raise ValueError("Thermocouple open circuit or error")
            
            # Extract temperature data (14-bit resolution)
            temp = (value >> 3) & 0xFFF
            raw_temp = temp * 0.25
            
            # Apply calibration if available
            calibrated_temp = self.calibration_manager.apply_calibration(
                self.sensor_name, raw_temp
            )
            
            return calibrated_temp
            
        except Exception as e:
            GPIO.output(self.cs_pin, GPIO.HIGH)  # Ensure CS is high on error
            raise e
    
    def test_sensor_connection(self):
        """Test if sensor is responding properly"""
        try:
            temp = self.read_temp_c()
            print(f"Sensor '{self.sensor_name}' test: {temp:.2f}°C")
            return True
        except Exception as e:
            print(f"Sensor '{self.sensor_name}' test failed: {e}")
            return False
    
    def read_multiple_samples(self, num_samples=5, delay=0.1):
        """Read multiple samples to check sensor stability"""
        samples = []
        for i in range(num_samples):
            try:
                temp = self.read_temp_c()
                samples.append(temp)
                time.sleep(delay)
            except Exception as e:
                print(f"Sample {i+1} failed: {e}")
                samples.append(None)
        return samples
    
    def get_calibration_status(self):
        """Get calibration status for this sensor"""
        return self.calibration_manager.get_calibration_status(self.sensor_name)
    
    def add_calibration_point(self, actual_temp: float, measured_temp: float):
        """Add a calibration point for this sensor"""
        self.calibration_manager.add_calibration_point(
            self.sensor_name, actual_temp, measured_temp
        )
        print(f"Added calibration point for {self.sensor_name}: actual={actual_temp}°C, measured={measured_temp}°C")
    
    def clear_calibration(self):
        """Clear calibration for this sensor"""
        self.calibration_manager.clear_calibration(self.sensor_name)
        print(f"Cleared calibration for {self.sensor_name}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup(self.cs_pin)