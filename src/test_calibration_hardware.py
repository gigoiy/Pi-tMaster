#!/usr/bin/env python3
# test_calibration_hardware.py
import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from max6675_simple import MAX6675

def test_hardware_calibration():
    """Test calibration with real MAX6675 hardware"""
    
    # Test sensor configuration - adjust CS pin as needed
    cs_pin = 8  # Change this to match your test sensor
    sensor_name = "test_sensor"
    
    print("=== MAX6675 Hardware Calibration Test ===")
    print(f"Testing sensor on CS pin {cs_pin}")
    
    try:
        # Initialize sensor
        sensor = MAX6675(cs_pin, sensor_name)
        
        # Test sensor connection
        if not sensor.test_sensor_connection():
            print("❌ Sensor test failed - check wiring")
            return
        
        print("✅ Sensor connected successfully")
        
        # Read multiple samples to check stability
        print("\n=== Reading multiple samples ===")
        samples = sensor.read_multiple_samples(5, 0.5)
        print(f"Samples: {samples}")
        
        # Show current calibration status
        print("\n=== Current Calibration Status ===")
        status = sensor.get_calibration_status()
        print(f"Calibrated: {status['is_calibrated']}")
        print(f"Points: {status['points_count']}/3")
        if status['is_calibrated']:
            print(f"Slope: {status['slope']:.4f}")
            print(f"Intercept: {status['intercept']:.4f}")
        
        # Example calibration process
        print("\n=== Calibration Example ===")
        print("To calibrate your sensor:")
        print("1. Place sensor in known temperature environment (ice bath, boiling water, etc.)")
        print("2. Use a reference thermometer to get the actual temperature")
        print("3. Call sensor.add_calibration_point(actual_temp, measured_temp)")
        print("4. Repeat for 3 different temperatures")
        print("5. The system will automatically calculate calibration coefficients")
        
        # Example: If you had calibration data, you would do:
        # sensor.add_calibration_point(0.0, current_reading)  # Ice bath
        # sensor.add_calibration_point(100.0, current_reading)  # Boiling water
        # etc.
        
        # Clean up
        sensor.cleanup()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your wiring:")
        print("- VCC to 3.3V or 5V")
        print("- GND to Ground")
        print("- CS to GPIO pin")
        print("- SO to MISO (GPIO9)")
        print("- SCK to SCLK (GPIO11)")

if __name__ == "__main__":
    test_hardware_calibration()