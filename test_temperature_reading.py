#!/usr/bin/env python3
"""
Tests for basic CPU temperature reading functionality.
Starting with just reading temperatures - these should fail since get_cpu_temperatures() doesn't exist yet.
"""

import unittest
from unittest.mock import patch, MagicMock
import cpu_freq_monitor

class TestTemperatureReading(unittest.TestCase):

    def test_get_cpu_temperatures_function_exists(self):
        """Test that get_cpu_temperatures function exists."""
        # This should fail since the function doesn't exist yet
        self.assertTrue(hasattr(cpu_freq_monitor, 'get_cpu_temperatures'))

    def test_get_cpu_temperatures_with_coretemp_sensors(self):
        """Test reading temperatures from coretemp sensors (Intel)."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_sensors:
            # Mock Intel coretemp sensor data
            mock_sensors.return_value = {
                'coretemp': [
                    MagicMock(label='Package id 0', current=65.0),
                    MagicMock(label='Core 0', current=60.0),
                    MagicMock(label='Core 1', current=62.0),
                    MagicMock(label='Core 2', current=58.0),
                    MagicMock(label='Core 3', current=61.0),
                ]
            }
            
            # This function doesn't exist yet - should fail
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            # Expected: function should return temperatures for all logical cores
            # With hyperthreading, this maps to 8 logical cores (2 per physical core)
            self.assertEqual(len(temps), 8)  # 8 logical cores
            self.assertEqual(temps, [60.0, 60.0, 62.0, 62.0, 58.0, 58.0, 61.0, 61.0])

    def test_get_cpu_temperatures_with_k10temp_sensors(self):
        """Test reading temperatures from k10temp sensors (AMD)."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_sensors:
            # Mock AMD k10temp sensor data
            mock_sensors.return_value = {
                'k10temp': [
                    MagicMock(label='Tctl', current=68.0),
                    MagicMock(label='Tccd1', current=65.0),
                    MagicMock(label='Tccd2', current=67.0),
                ]
            }
            
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            # Expected: function should handle AMD sensors
            self.assertIsNotNone(temps)
            self.assertGreater(len(temps), 0)

    def test_get_cpu_temperatures_no_sensors_available(self):
        """Test graceful handling when no temperature sensors are found."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_sensors:
            mock_sensors.return_value = {}  # No sensors
            
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            # Expected: should return None or empty list gracefully
            self.assertIsNone(temps)

    def test_get_cpu_temperatures_psutil_exception(self):
        """Test handling when psutil.sensors_temperatures() throws exception."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_sensors:
            mock_sensors.side_effect = Exception("Sensor access denied")
            
            # Should not crash, should return None
            temps = cpu_freq_monitor.get_cpu_temperatures()
            self.assertIsNone(temps)

    def test_get_cpu_temperatures_returns_reasonable_values(self):
        """Test that returned temperatures are within reasonable range."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_sensors, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock 4 logical cores from 2 physical cores
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            mock_sensors.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=45.5),
                    MagicMock(label='Core 1', current=102.3),  # Very high
                    MagicMock(label='Core 2', current=-5.0),   # Invalid negative
                ]
            }
            
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            # Function should validate temperature ranges and map to logical cores
            self.assertIsNotNone(temps)
            self.assertEqual(len(temps), 4)  # 4 logical cores
            for temp in temps:
                if temp is not None:  # Allow None for invalid readings
                    self.assertGreaterEqual(temp, 0)    # No negative temps
                    self.assertLessEqual(temp, 150)     # Reasonable max

    def test_temperature_constants_exist(self):
        """Test that temperature threshold constants are defined."""
        # These don't exist yet - should fail
        self.assertTrue(hasattr(cpu_freq_monitor, 'TEMPERATURE_WARNING_THRESHOLD'))
        self.assertTrue(hasattr(cpu_freq_monitor, 'TEMPERATURE_CRITICAL_THRESHOLD'))

    def test_temperature_constants_values(self):
        """Test that temperature thresholds have reasonable values."""
        # Should fail since constants don't exist
        self.assertEqual(cpu_freq_monitor.TEMPERATURE_WARNING_THRESHOLD, 80)
        self.assertEqual(cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD, 90)
        
        # Warning should be less than critical
        self.assertLess(
            cpu_freq_monitor.TEMPERATURE_WARNING_THRESHOLD,
            cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD
        )

    def test_integration_with_existing_functions(self):
        """Test that temperature reading works alongside existing functions."""
        with patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_temps, \
             patch('cpu_freq_monitor.psutil.cpu_freq') as mock_freq, \
             patch('cpu_freq_monitor.psutil.cpu_percent') as mock_usage, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock all three data sources
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 2500.0
            mock_freq_obj.max = 3000.0
            mock_freq.return_value = [mock_freq_obj, mock_freq_obj]
            mock_usage.return_value = [25.0, 30.0]
            mock_temps.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=65.0),
                    MagicMock(label='Core 1', current=68.0),
                ]
            }
            # Mock CPU topology for temperature mapping
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2  # 4 logical, 2 physical cores
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            # All three should work independently
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            usage = cpu_freq_monitor.get_cpu_usage()
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            self.assertEqual(freqs, [2500.0, 2500.0])
            self.assertEqual(usage, [25.0, 30.0])
            # With 2 physical cores mapped to 4 logical cores
            self.assertEqual(temps, [65.0, 65.0, 68.0, 68.0])

    def test_simple_temperature_display_format(self):
        """Test basic temperature display formatting."""
        # Test the format we'd use to display temperatures
        temp_value = 67.5
        
        # Simple formatting tests
        formatted = f"{temp_value:.1f}°C"
        self.assertEqual(formatted, "67.5°C")
        
        formatted_int = f"{temp_value:.0f}°C"
        self.assertEqual(formatted_int, "68°C")

if __name__ == '__main__':
    print("Running basic temperature reading tests...")
    print("These tests SHOULD FAIL since get_cpu_temperatures() doesn't exist yet.")
    print("=" * 65)
    unittest.main(verbosity=2)