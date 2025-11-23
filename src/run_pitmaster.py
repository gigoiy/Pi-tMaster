#!/usr/bin/env python3
# run_pitmaster.py

import os
import subprocess
import time
import threading
from flask import Flask, jsonify, render_template, request
import RPi.GPIO as GPIO
from max6675_simple import MAX6675

def create_app():
    # Define CS pins (BCM numbering)
    cs_pins = {
        "smoker_left": 8,    # GPIO8 (BCM) - Pin 24
        "smoker_right": 7,   # GPIO7 (BCM) - Pin 26
        "meat_probe": 16     # GPIO16 (BCM) - Pin 36
    }

    # Create sensor objects for real hardware
    sensors = {}
    sensor_status = {}
    
    # Temporary simulation mode for testing
    SIMULATION_MODE = True  # Set to True to enable temperature simulation
    simulated_temps = {
        "smoker_left": 25.0,
        "smoker_right": 25.0, 
        "meat_probe": 25.0
    }
    
    print("Initializing MAX6675 sensors...")
    for name, cs_pin in cs_pins.items():
        try:
            sensors[name] = MAX6675(cs_pin, sensor_name=name)
            # Test sensor connection
            if sensors[name].test_sensor_connection():
                sensor_status[name] = "Connected"
                print(f"✓ {name} initialized successfully")
            else:
                sensor_status[name] = "Connection Error"
                print(f"✗ {name} failed to initialize")
        except Exception as e:
            sensors[name] = None
            sensor_status[name] = f"Error: {str(e)}"
            print(f"✗ Failed to initialize {name}: {e}")

    temperature_data = {
        "smoker_left": {"temp_c": 0.0, "temp_f": 0.0, "raw_temp_c": 0.0, "error": None},
        "smoker_right": {"temp_c": 0.0, "temp_f": 0.0, "raw_temp_c": 0.0, "error": None},
        "meat_probe": {"temp_c": 0.0, "temp_f": 0.0, "raw_temp_c": 0.0, "error": None},
        "last_updated": "",
        "sensor_status": sensor_status,
        "simulation_mode": SIMULATION_MODE
    }

    app = Flask(__name__)

    def read_cpufreq_status():
        # Read CPU frequency settings using helper script
        try:
            # Use full path to sudo for reliability
            result = subprocess.run(
                ['/usr/bin/sudo', '/usr/local/bin/cpu-power-helper.sh', 'get-status'],
                capture_output=True, text=True, check=True, timeout=10
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 4:
                return {
                    'governor': lines[0],
                    'cur_freq': lines[1],
                    'min_freq': lines[2],
                    'max_freq': lines[3]
                }
            else:
                raise Exception(f"Invalid response from helper script. Got {len(lines)} lines, expected 4")
        except subprocess.TimeoutExpired:
            raise Exception("Helper script timeout - check if helper script is installed correctly")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Helper script error (code {e.returncode}): {e.stderr}")
        except FileNotFoundError:
            raise Exception("sudo or helper script not found - check installation")
        except Exception as e:
            raise Exception(f"Failed to read CPU settings: {str(e)}")

    def set_cpufreq_mode(mode):
        # Set CPU frequency mode using helper script
        try:
            if mode == 'powersave':
                cmd = ['/usr/bin/sudo', '/usr/local/bin/cpu-power-helper.sh', 'set-powersave']
            elif mode == 'ondemand':
                cmd = ['/usr/bin/sudo', '/usr/local/bin/cpu-power-helper.sh', 'set-ondemand']
            else:
                raise ValueError("Invalid mode")
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=10
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("Helper script timeout - check if helper script is installed correctly")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Helper script error (code {e.returncode}): {e.stderr}")
        except FileNotFoundError:
            raise Exception("sudo or helper script not found - check installation")
        except Exception as e:
            raise Exception(f"Failed to set CPU settings: {str(e)}")

    def read_sensors_loop():
        while True:
            for name, sensor in sensors.items():
                try:
                    if SIMULATION_MODE:
                        # Use simulated temperature for testing
                        raw_temp_c = simulated_temps[name]
                        temp_c = raw_temp_c
                    else:
                        # Read from actual hardware
                        if sensor is not None:
                            raw_temp_c = sensor.read_temp_c()
                            temp_c = raw_temp_c
                        else:
                            temperature_data[name]["error"] = "Sensor not initialized"
                            continue
                    
                    temp_f = temp_c * 9/5 + 32
                    temperature_data[name]["temp_c"] = round(temp_c, 2)
                    temperature_data[name]["temp_f"] = round(temp_f, 2)
                    temperature_data[name]["raw_temp_c"] = round(raw_temp_c, 2)
                    temperature_data[name]["error"] = None
                    
                except Exception as e:
                    temperature_data[name]["error"] = str(e)
                    print(f"[ERROR] Reading {name}: {e}")
            
            temperature_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(3)  # Read sensors every 3 seconds

    # Route for temperature monitoring page
    @app.route('/')
    @app.route('/temperature')
    def temperature():
        return render_template('temperature.html')

    # Route for calibration page
    @app.route('/calibration')
    def calibration():
        return render_template('calibration.html')

    # Route for power management page
    @app.route('/power')
    def power():
        return render_template('power.html')

    # Route for simulation testing page
    @app.route('/simulation')
    def simulation():
        return render_template('simulation.html')

    @app.route('/data')
    def get_data():
        return jsonify(temperature_data)
    
    @app.route('/powerstatus')
    def powerstatus():
        # Check current power status using helper script
        try:
            cpufreq = read_cpufreq_status()
            governor = cpufreq['governor']
            cur_freq = int(cpufreq['cur_freq']) // 1000
            min_freq = int(cpufreq['min_freq']) // 1000
            max_freq = int(cpufreq['max_freq']) // 1000
        
            power_mode = "LOW POWER 24/7" if governor == "powersave" else "FULL POWER"
        
            return jsonify({
                "power_mode": power_mode,
                "cpu_governor": governor,
                "cpu_cur_freq": cur_freq,
                "cpu_min_freq": min_freq,
                "cpu_max_freq": max_freq,
                "status": "Running"
            })
        except Exception as e:
            print(f"ERROR in powerstatus: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
    @app.route('/enable-low-power')
    def enable_low_power():
        # Enable low power mode using helper script
        try:
            result = set_cpufreq_mode('powersave')
            if result == "OK":
                return "Low power mode enabled successfully"
            else:
                return f"Unexpected response: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/enable-full-power')
    def enable_full_power():
        # Enable full power mode using helper script
        try:
            result = set_cpufreq_mode('ondemand')
            if result == "OK":
                return "Full power mode enabled successfully"
            else:
                return f"Unexpected response: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/shutdown')
    def shutdown():
        # Manual shutdown endpoint
        try:
            subprocess.run(['/usr/bin/sudo', 'shutdown', 'now'], check=True)
            return "System is shutting down..."
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/reboot')
    def reboot():
        # Manual reboot endpoint
        try:
            subprocess.run(['/usr/bin/sudo', 'reboot'], check=True)
            return "System is rebooting..."
        except Exception as e:
            return f"Error: {str(e)}"

    # Calibration endpoints
    @app.route('/calibration/status')
    def calibration_status():
        """Get calibration status for all sensors"""
        status = {}
        for name, sensor in sensors.items():
            if sensor is not None:
                status[name] = sensor.get_calibration_status()
            else:
                status[name] = {"error": "Sensor not available"}
        return jsonify(status)
    
    @app.route('/calibration/add_point', methods=['POST'])
    def add_calibration_point():
        """Add a calibration point for a sensor"""
        try:
            data = request.get_json()
            sensor_name = data.get('sensor_name')
            actual_temp = float(data.get('actual_temp'))
            
            if sensor_name in sensors and sensors[sensor_name] is not None:
                # Use current sensor reading as measured temperature
                measured_temp = sensors[sensor_name].read_temp_c()
                
                sensors[sensor_name].add_calibration_point(actual_temp, measured_temp)
                return jsonify({
                    "status": "success", 
                    "message": f"Calibration point added: actual={actual_temp}°C, measured={measured_temp:.2f}°C"
                })
            else:
                return jsonify({"status": "error", "message": "Invalid sensor name or sensor not available"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
    
    @app.route('/calibration/add_point_manual', methods=['POST'])
    def add_calibration_point_manual():
        """Add a calibration point with manual measured temperature"""
        try:
            data = request.get_json()
            sensor_name = data.get('sensor_name')
            actual_temp = float(data.get('actual_temp'))
            measured_temp = float(data.get('measured_temp'))
            
            if sensor_name in sensors and sensors[sensor_name] is not None:
                sensors[sensor_name].add_calibration_point(actual_temp, measured_temp)
                return jsonify({
                    "status": "success", 
                    "message": f"Calibration point added: actual={actual_temp}°C, measured={measured_temp}°C"
                })
            else:
                return jsonify({"status": "error", "message": "Invalid sensor name or sensor not available"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
    
    @app.route('/calibration/clear', methods=['POST'])
    def clear_calibration():
        """Clear calibration for a sensor"""
        try:
            data = request.get_json()
            sensor_name = data.get('sensor_name')
            
            if sensor_name in sensors and sensors[sensor_name] is not None:
                sensors[sensor_name].clear_calibration()
                return jsonify({"status": "success", "message": "Calibration cleared"})
            else:
                return jsonify({"status": "error", "message": "Invalid sensor name or sensor not available"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route('/sensor/test')
    def test_sensors():
        """Test all sensors and return their status"""
        results = {}
        for name, sensor in sensors.items():
            if sensor is not None:
                results[name] = {
                    "status": "Testing...",
                    "samples": sensor.read_multiple_samples(3, 0.5)
                }
            else:
                results[name] = {"status": "Not available"}
        return jsonify(results)

    # Simulation endpoints for testing
    @app.route('/simulation/set_temperature', methods=['POST'])
    def set_simulated_temperature():
        """Set simulated temperature for a sensor (for testing only)"""
        try:
            data = request.get_json()
            sensor_name = data.get('sensor_name')
            temperature = float(data.get('temperature'))
            
            if sensor_name in simulated_temps:
                # Test for integer overflow and range limits
                if temperature < -273.15:  # Absolute zero
                    return jsonify({"status": "error", "message": "Temperature below absolute zero"}), 400
                
                # Type-K thermocouple range: -200°C to +1350°C
                if temperature < -200 or temperature > 1350:
                    return jsonify({
                        "status": "warning", 
                        "message": f"Temperature {temperature}°C outside Type-K range (-200°C to +1350°C)"
                    })
                
                simulated_temps[sensor_name] = temperature
                return jsonify({
                    "status": "success", 
                    "message": f"Set {sensor_name} to {temperature}°C"
                })
            else:
                return jsonify({"status": "error", "message": "Invalid sensor name"}), 400
                
        except ValueError as e:
            return jsonify({"status": "error", "message": "Invalid temperature value"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route('/simulation/set_all', methods=['POST'])
    def set_all_simulated_temperatures():
        """Set all sensors to the same temperature (for testing only)"""
        try:
            data = request.get_json()
            temperature = float(data.get('temperature'))
            
            # Test for integer overflow and range limits
            if temperature < -273.15:  # Absolute zero
                return jsonify({"status": "error", "message": "Temperature below absolute zero"}), 400
            
            # Type-K thermocouple range: -200°C to +1350°C
            if temperature < -200 or temperature > 1350:
                return jsonify({
                    "status": "warning", 
                    "message": f"Temperature {temperature}°C outside Type-K range (-200°C to +1350°C)"
                })
            
            for sensor_name in simulated_temps.keys():
                simulated_temps[sensor_name] = temperature
                
            return jsonify({
                "status": "success", 
                "message": f"Set all sensors to {temperature}°C"
            })
                
        except ValueError as e:
            return jsonify({"status": "error", "message": "Invalid temperature value"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route('/simulation/test_extremes', methods=['POST'])
    def test_temperature_extremes():
        """Test extreme temperature values (for testing only)"""
        try:
            test_cases = [
                {"name": "Absolute Minimum", "temp": -200.0},
                {"name": "Freezing", "temp": 0.0},
                {"name": "Room Temperature", "temp": 25.0},
                {"name": "Boiling", "temp": 100.0},
                {"name": "Type-K Maximum", "temp": 1350.0},
                {"name": "Below Absolute Zero", "temp": -300.0},
                {"name": "Above Type-K Max", "temp": 1500.0},
                {"name": "Very Large Number", "temp": 999999.0},
                {"name": "Very Small Number", "temp": -999999.0}
            ]
            
            results = []
            for test_case in test_cases:
                try:
                    # Test individual sensor setting
                    simulated_temps["smoker_left"] = test_case["temp"]
                    temp_c = simulated_temps["smoker_left"]
                    temp_f = temp_c * 9/5 + 32
                    
                    results.append({
                        "test_case": test_case["name"],
                        "temp_c": temp_c,
                        "temp_f": temp_f,
                        "status": "success",
                        "json_response": f"C: {temp_c:.2f}, F: {temp_f:.2f}"
                    })
                    
                except Exception as e:
                    results.append({
                        "test_case": test_case["name"],
                        "temp_c": test_case["temp"],
                        "status": "error",
                        "error": str(e)
                    })
            
            return jsonify({
                "status": "success",
                "results": results,
                "message": f"Tested {len(results)} extreme temperature cases"
            })
                
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    @app.route('/simulation/status')
    def get_simulation_status():
        """Get current simulation status"""
        return jsonify({
            "simulation_mode": SIMULATION_MODE,
            "current_temperatures": simulated_temps,
            "type_k_range": {"min": -200, "max": 1350},
            "absolute_zero": -273.15
        })

    # Start sensor reading thread
    sensor_thread = threading.Thread(target=read_sensors_loop, daemon=True)
    sensor_thread.start()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080)