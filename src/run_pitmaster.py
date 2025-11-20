#!/usr/bin/env python3
# run_pitmaster.py

import os
import subprocess
import time
import threading
from flask import Flask, jsonify, render_template
import RPi.GPIO as GPIO
from max6675_simple import MAX6675

def create_app():
    # Define CS pins (BCM numbering)
    cs_pins = {
        "smoker_left": 8,    # GPIO8 (BCM)
        "smoker_right": 7,   # GPIO7 (BCM) 
        "meat_probe": 16     # GPIO16 (BCM)
    }

    # Create sensor objects
    sensors = {}
    for name, cs_pin in cs_pins.items():
        sensors[name] = MAX6675(cs_pin)

    temperature_data = {
        "smoker_left": {"temp_c": 0.0, "temp_f": 0.0},
        "smoker_right": {"temp_c": 0.0, "temp_f": 0.0},
        "meat_probe": {"temp_c": 0.0, "temp_f": 0.0},
        "last_updated": ""
    }

    app = Flask(__name__)

    def read_cpufreq_status():
        # Read CPU frequency settings using helper script
        try:
            # Use full path to sudo for reliability
            result = subprocess.run(
                'sudo /usr/local/bin/cpu-power-helper.sh get-status',
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
                cmd = 'sudo /usr/local/bin/cpu-power-helper.sh set-powersave'
            elif mode == 'ondemand':
                cmd = 'sudo /usr/bin/local/cpu-power-helper.sh set-ondemand'
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
                    temp_c = sensor.read_temp_c()
                    temp_f = temp_c * 9/5 + 32
                    temperature_data[name]["temp_c"] = round(temp_c, 2)
                    temperature_data[name]["temp_f"] = round(temp_f, 2)
                except Exception as e:
                    print(f"[WARN] Error reading {name}: {e}")
            temperature_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(3)

    @app.route('/')
    def index():
        return render_template('index.html')

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
            print(f"ERROR in powerstatus: {str(e)}")  # Debug logging
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
            subprocess.run("sudo shutdown -h now", check=True)
            return "System is shutting down..."
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/reboot')
    def reboot():
        # Manual reboot endpoint
        try:
            subprocess.run("sudo reboot", check=True)
            return "System is rebooting..."
        except Exception as e:
            return f"Error: {str(e)}"

    sensor_thread = threading.Thread(target=read_sensors_loop, daemon=True)
    sensor_thread.start()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080)