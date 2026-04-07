#!/usr/bin/env python3
"""
Test the background color behavior for critical alerts.
"""

import unittest
from unittest.mock import patch, MagicMock
import cpu_freq_monitor
from collections import deque

class TestBackgroundBehavior(unittest.TestCase):

    def test_normal_conditions_no_red_background(self):
        """Test that normal conditions don't trigger red background."""
        with patch('cpu_freq_monitor.psutil.cpu_freq') as mock_freq, \
             patch('cpu_freq_monitor.psutil.cpu_percent') as mock_usage, \
             patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_temps, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock normal conditions
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 2500.0  # Normal frequency
            mock_freq_obj.max = 3000.0
            mock_freq.return_value = [mock_freq_obj, mock_freq_obj]
            mock_usage.return_value = [25.0, 30.0]  # Normal usage
            mock_temps.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=65.0),  # Normal temp
                    MagicMock(label='Core 1', current=68.0),  # Normal temp
                ]
            }
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            # Get data and create histories
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            usage = cpu_freq_monitor.get_cpu_usage()
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            freq_hist = [deque([f], maxlen=60) for f in freqs]
            usage_hist = [deque([u], maxlen=60) for u in usage]
            temp_hist = [deque(maxlen=60) for _ in range(len(freqs))]
            
            # Add temp data
            for i, temp in enumerate(temps):
                if i < len(temp_hist):
                    temp_hist[i].append(temp)
            
            # Check alerts
            alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(freq_hist, usage_hist, max_freq)
            
            # Check temperature averages
            avg_temps = []
            for th in temp_hist:
                if len(th) > 0:
                    avg_temps.append(sum(th) / len(th))
                else:
                    avg_temps.append(None)
            
            # Simulate critical alert logic
            critical_alert = False
            if alert_type == "throttling":
                critical_alert = True
            for temp in avg_temps:
                if temp is not None and temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                    critical_alert = True
                    break
            
            # Should NOT have red background
            self.assertFalse(critical_alert)
            self.assertEqual(alert_type, "normal")

    def test_throttling_triggers_red_background(self):
        """Test that throttling triggers red background."""
        with patch('cpu_freq_monitor.psutil.cpu_freq') as mock_freq, \
             patch('cpu_freq_monitor.psutil.cpu_percent') as mock_usage, \
             patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_temps, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock throttling conditions
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 1200.0  # Low frequency (throttling)
            mock_freq_obj.max = 3000.0
            mock_freq.return_value = [mock_freq_obj, mock_freq_obj]
            mock_usage.return_value = [25.0, 30.0]
            mock_temps.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=65.0),  # Normal temp
                    MagicMock(label='Core 1', current=68.0),  # Normal temp
                ]
            }
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            # Get data and create histories
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            usage = cpu_freq_monitor.get_cpu_usage()
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            freq_hist = [deque([f], maxlen=60) for f in freqs]
            usage_hist = [deque([u], maxlen=60) for u in usage]
            temp_hist = [deque(maxlen=60) for _ in range(len(freqs))]
            
            # Add temp data
            for i, temp in enumerate(temps):
                if i < len(temp_hist):
                    temp_hist[i].append(temp)
            
            # Check alerts
            alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(freq_hist, usage_hist, max_freq)
            
            # Check temperature averages
            avg_temps = []
            for th in temp_hist:
                if len(th) > 0:
                    avg_temps.append(sum(th) / len(th))
                else:
                    avg_temps.append(None)
            
            # Simulate critical alert logic
            critical_alert = False
            if alert_type == "throttling":
                critical_alert = True
            for temp in avg_temps:
                if temp is not None and temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                    critical_alert = True
                    break
            
            # SHOULD have red background due to throttling
            self.assertTrue(critical_alert)
            self.assertEqual(alert_type, "throttling")

    def test_critical_temperature_triggers_red_background(self):
        """Test that critical temperature triggers red background."""
        with patch('cpu_freq_monitor.psutil.cpu_freq') as mock_freq, \
             patch('cpu_freq_monitor.psutil.cpu_percent') as mock_usage, \
             patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_temps, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock critical temperature conditions
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 2500.0  # Normal frequency
            mock_freq_obj.max = 3000.0
            mock_freq.return_value = [mock_freq_obj, mock_freq_obj]
            mock_usage.return_value = [25.0, 30.0]
            mock_temps.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=95.0),  # CRITICAL temp!
                    MagicMock(label='Core 1', current=68.0),  # Normal temp
                ]
            }
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            # Get data and create histories
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            usage = cpu_freq_monitor.get_cpu_usage()
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            freq_hist = [deque([f], maxlen=60) for f in freqs]
            usage_hist = [deque([u], maxlen=60) for u in usage]
            temp_hist = [deque(maxlen=60) for _ in range(len(freqs))]
            
            # Add temp data
            for i, temp in enumerate(temps):
                if i < len(temp_hist):
                    temp_hist[i].append(temp)
            
            # Check alerts
            alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(freq_hist, usage_hist, max_freq)
            
            # Check temperature averages
            avg_temps = []
            for th in temp_hist:
                if len(th) > 0:
                    avg_temps.append(sum(th) / len(th))
                else:
                    avg_temps.append(None)
            
            # Simulate critical alert logic
            critical_alert = False
            if alert_type == "throttling":
                critical_alert = True
            for temp in avg_temps:
                if temp is not None and temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                    critical_alert = True
                    break
            
            # SHOULD have red background due to critical temperature
            self.assertTrue(critical_alert)
            # Should find the critical temperature
            self.assertTrue(any(t >= 90.0 for t in avg_temps if t is not None))

    def test_high_usage_does_not_trigger_red_background(self):
        """Test that high CPU usage (>90%) does NOT trigger red background."""
        with patch('cpu_freq_monitor.psutil.cpu_freq') as mock_freq, \
             patch('cpu_freq_monitor.psutil.cpu_percent') as mock_usage, \
             patch('cpu_freq_monitor.psutil.sensors_temperatures') as mock_temps, \
             patch('cpu_freq_monitor.psutil.cpu_count') as mock_cpu_count:
            
            # Mock high usage conditions
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 2500.0  # Normal frequency
            mock_freq_obj.max = 3000.0
            mock_freq.return_value = [mock_freq_obj, mock_freq_obj]
            mock_usage.return_value = [95.0, 98.0]  # HIGH usage
            mock_temps.return_value = {
                'coretemp': [
                    MagicMock(label='Core 0', current=65.0),  # Normal temp
                    MagicMock(label='Core 1', current=68.0),  # Normal temp
                ]
            }
            def cpu_count_side_effect(logical=True):
                return 4 if logical else 2
            mock_cpu_count.side_effect = cpu_count_side_effect
            
            # Get data and create histories
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            usage = cpu_freq_monitor.get_cpu_usage()
            temps = cpu_freq_monitor.get_cpu_temperatures()
            
            freq_hist = [deque([f], maxlen=60) for f in freqs]
            usage_hist = [deque([u], maxlen=60) for u in usage]
            temp_hist = [deque(maxlen=60) for _ in range(len(freqs))]
            
            # Add temp data
            for i, temp in enumerate(temps):
                if i < len(temp_hist):
                    temp_hist[i].append(temp)
            
            # Check alerts
            alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(freq_hist, usage_hist, max_freq)
            
            # Check temperature averages
            avg_temps = []
            for th in temp_hist:
                if len(th) > 0:
                    avg_temps.append(sum(th) / len(th))
                else:
                    avg_temps.append(None)
            
            # Simulate critical alert logic
            critical_alert = False
            if alert_type == "throttling":
                critical_alert = True
            for temp in avg_temps:
                if temp is not None and temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                    critical_alert = True
                    break
            
            # Should NOT have red background despite high usage
            self.assertFalse(critical_alert)
            # But should detect high usage
            self.assertTrue(any(u >= 90.0 for u in avg_usage))


if __name__ == '__main__':
    print("Testing background behavior for critical alerts...")
    print("=" * 60)
    unittest.main(verbosity=2)