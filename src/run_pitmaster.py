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
        # Check current power status
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                governor = f.read().strip()
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
                cur_freq = int(f.read().strip()) // 1000
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq', 'r') as f:
                min_freq = int(f.read().strip()) // 1000
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'r') as f:
                max_freq = int(f.read().strip()) // 1000
        
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
            return jsonify({"error": str(e)}), 500
        
    @app.route('/enable-low-power')
    def enable_low_power():
        # Enable low power mode
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'w') as f:
                f.write('powersave')
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq', 'w') as f:
                f.write('300000')
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'w') as f:
                f.write('600000')
            return "Low power mode enabled"
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/enable-full-power')
    def enable_full_power():
        # Enable full power mode
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'w') as f:
                f.write('ondemand')
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq', 'w') as f:
                f.write('600000')  # 600 MHz min
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'w') as f:
                f.write('1500000')  # 1.5 GHz max for Pi 4
            return "Full power mode enabled"
        except Exception as e:
            return f"Error: {str(e)}"

    @app.route('/shutdown')
    def shutdown():
        # Manual shutdown endpoint
        import subprocess
        subprocess.run(["sudo", "shutdown", "-h", "now"])
        return "System is shutting down..."

    @app.route('/reboot')
    def reboot():
        # Manual reboot endpoint
        import subprocess
        subprocess.run(["sudo", "reboot"])
        return "System is rebooting..."

    sensor_thread = threading.Thread(target=read_sensors_loop, daemon=True)
    sensor_thread.start()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080)