# calibration.py
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CalibrationPoint:
    actual_temp: float
    measured_temp: float
    timestamp: float

@dataclass
class SensorCalibration:
    sensor_name: str
    points: List[CalibrationPoint]
    slope: float = 1.0
    intercept: float = 0.0
    is_calibrated: bool = False

class CalibrationManager:
    def __init__(self, calibration_file="calibration_data.json"):
        self.calibration_file = calibration_file
        self.calibrations: Dict[str, SensorCalibration] = {}
        self.load_calibrations()
    
    def load_calibrations(self):
        """Load calibration data from file"""
        try:
            if os.path.exists(self.calibration_file):
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    for sensor_name, cal_data in data.items():
                        points = [CalibrationPoint(**point) for point in cal_data['points']]
                        self.calibrations[sensor_name] = SensorCalibration(
                            sensor_name=sensor_name,
                            points=points,
                            slope=cal_data.get('slope', 1.0),
                            intercept=cal_data.get('intercept', 0.0),
                            is_calibrated=cal_data.get('is_calibrated', False)
                        )
                print(f"Loaded calibrations for {len(self.calibrations)} sensors")
        except Exception as e:
            print(f"Error loading calibrations: {e}")
            self.calibrations = {}
    
    def save_calibrations(self):
        """Save calibration data to file"""
        try:
            data = {}
            for sensor_name, calibration in self.calibrations.items():
                data[sensor_name] = {
                    'points': [{'actual_temp': p.actual_temp, 
                              'measured_temp': p.measured_temp, 
                              'timestamp': p.timestamp} 
                             for p in calibration.points],
                    'slope': calibration.slope,
                    'intercept': calibration.intercept,
                    'is_calibrated': calibration.is_calibrated
                }
            with open(self.calibration_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving calibrations: {e}")
    
    def add_calibration_point(self, sensor_name: str, actual_temp: float, measured_temp: float):
        """Add a calibration point for a sensor"""
        if sensor_name not in self.calibrations:
            self.calibrations[sensor_name] = SensorCalibration(
                sensor_name=sensor_name,
                points=[]
            )
        
        point = CalibrationPoint(
            actual_temp=actual_temp,
            measured_temp=measured_temp,
            timestamp=time.time()
        )
        
        self.calibrations[sensor_name].points.append(point)
        
        # Keep only the 3 most recent points
        if len(self.calibrations[sensor_name].points) > 3:
            self.calibrations[sensor_name].points = self.calibrations[sensor_name].points[-3:]
        
        # Recalculate calibration curve if we have 3 points
        if len(self.calibrations[sensor_name].points) == 3:
            self._calculate_calibration(sensor_name)
        
        self.save_calibrations()
    
    def _calculate_calibration(self, sensor_name: str):
        """Calculate linear calibration curve using 3 points"""
        try:
            cal = self.calibrations[sensor_name]
            points = cal.points
            
            # Simple linear regression for 3 points
            x = [p.measured_temp for p in points]
            y = [p.actual_temp for p in points]
            
            # Calculate slope and intercept using least squares
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] * x[i] for i in range(n))
            
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator != 0:
                cal.slope = (n * sum_xy - sum_x * sum_y) / denominator
                cal.intercept = (sum_y - cal.slope * sum_x) / n
                cal.is_calibrated = True
                print(f"Calibrated {sensor_name}: slope={cal.slope:.4f}, intercept={cal.intercept:.4f}")
            else:
                print(f"Calibration failed for {sensor_name}: division by zero")
                
        except Exception as e:
            print(f"Error calculating calibration for {sensor_name}: {e}")
    
    def apply_calibration(self, sensor_name: str, raw_temp: float) -> float:
        """Apply calibration to a raw temperature reading"""
        if (sensor_name in self.calibrations and 
            self.calibrations[sensor_name].is_calibrated):
            cal = self.calibrations[sensor_name]
            calibrated_temp = cal.slope * raw_temp + cal.intercept
            return calibrated_temp
        return raw_temp
    
    def get_calibration_status(self, sensor_name: str) -> Dict:
        """Get calibration status for a sensor"""
        if sensor_name in self.calibrations:
            cal = self.calibrations[sensor_name]
            return {
                'is_calibrated': cal.is_calibrated,
                'points_count': len(cal.points),
                'slope': cal.slope,
                'intercept': cal.intercept,
                'points': [{'actual_temp': p.actual_temp, 
                          'measured_temp': p.measured_temp,
                          'timestamp': p.timestamp} 
                         for p in cal.points]
            }
        return {'is_calibrated': False, 'points_count': 0}
    
    def clear_calibration(self, sensor_name: str):
        """Clear calibration for a sensor"""
        if sensor_name in self.calibrations:
            del self.calibrations[sensor_name]
            self.save_calibrations()