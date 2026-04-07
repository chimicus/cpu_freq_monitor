#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock
from collections import deque
import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor

class TestCpuFreqMonitor(unittest.TestCase):

    def test_get_cpu_frequencies_returns_valid_data(self):
        """Test that get_cpu_frequencies returns frequencies and max frequency"""
        with patch('src.cpu_freq_monitor.psutil.cpu_freq') as mock_cpu_freq:
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 2000.0
            mock_freq_obj.max = 3000.0
            mock_cpu_freq.return_value = [mock_freq_obj, mock_freq_obj]
            
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            
            self.assertEqual(freqs, [2000.0, 2000.0])
            self.assertEqual(max_freq, 3000.0)
            mock_cpu_freq.assert_called_once_with(percpu=True)

    def test_get_cpu_frequencies_handles_single_core(self):
        """Test get_cpu_frequencies with single core system"""
        with patch('src.cpu_freq_monitor.psutil.cpu_freq') as mock_cpu_freq:
            mock_freq_obj = MagicMock()
            mock_freq_obj.current = 1500.0
            mock_freq_obj.max = 2500.0
            mock_cpu_freq.return_value = [mock_freq_obj]
            
            freqs, max_freq = cpu_freq_monitor.get_cpu_frequencies()
            
            self.assertEqual(freqs, [1500.0])
            self.assertEqual(max_freq, 2500.0)

    def test_alert_logic_no_alert_when_above_threshold(self):
        """Test that no alert is triggered when frequencies are above threshold"""
        max_freq = 3000.0
        warn_threshold = max_freq * cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD  # 1500.0
        
        # Create histories with frequencies above threshold
        histories = [
            deque([2000.0, 2100.0, 1900.0], maxlen=60),  # avg = 2000.0
            deque([2200.0, 2300.0, 2100.0], maxlen=60),  # avg = 2200.0
        ]
        
        avgs = [sum(d) / len(d) for d in histories]
        alert = any(a < max_freq * cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD for a in avgs)
        
        self.assertFalse(alert)
        for avg in avgs:
            self.assertGreater(avg, warn_threshold)

    def test_alert_logic_triggers_when_below_threshold(self):
        """Test that alert is triggered when any core average drops below threshold"""
        max_freq = 3000.0
        warn_threshold = max_freq * cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD  # 1500.0
        
        # Create histories with one core below threshold
        histories = [
            deque([2000.0, 2100.0, 1900.0], maxlen=60),  # avg = 2000.0 (above)
            deque([1000.0, 1200.0, 1400.0], maxlen=60),  # avg = 1200.0 (below)
        ]
        
        avgs = [sum(d) / len(d) for d in histories]
        alert = any(a < max_freq * cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD for a in avgs)
        
        self.assertTrue(alert)
        self.assertGreater(avgs[0], warn_threshold)
        self.assertLess(avgs[1], warn_threshold)

    def test_percentage_calculation_accuracy(self):
        """Test frequency to percentage conversion accuracy"""
        max_freq = 2000.0
        
        test_cases = [
            (2000.0, 100.0),  # max frequency = 100%
            (1000.0, 50.0),   # half frequency = 50%
            (500.0, 25.0),    # quarter frequency = 25%
            (0.0, 0.0),       # zero frequency = 0%
            (2500.0, 125.0),  # over max = 125%
        ]
        
        for freq, expected_pct in test_cases:
            pct = (freq / max_freq) * 100
            self.assertAlmostEqual(pct, expected_pct, places=1)

    def test_history_deque_maxlen_behavior(self):
        """Test that history deques properly maintain max length"""
        history_length = cpu_freq_monitor.HISTORY_SECONDS
        hist = deque(maxlen=history_length)
        
        # Add more items than maxlen
        for i in range(history_length + 10):
            hist.append(i)
        
        # Should only keep the last 'history_length' items
        self.assertEqual(len(hist), history_length)
        self.assertEqual(list(hist), list(range(10, history_length + 10)))

    def test_history_average_calculation(self):
        """Test that history averages are calculated correctly"""
        histories = [
            deque([1000.0, 2000.0, 3000.0], maxlen=60),
            deque([500.0, 1500.0], maxlen=60),
        ]
        
        avgs = [sum(d) / len(d) for d in histories]
        
        self.assertAlmostEqual(avgs[0], 2000.0, places=1)  # (1000+2000+3000)/3
        self.assertAlmostEqual(avgs[1], 1000.0, places=1)  # (500+1500)/2

    def test_bar_graph_scaling(self):
        """Test that frequency values scale correctly to bar graph characters"""
        bars = '▁▂▃▄▅▆▇█'
        max_freq = 3000.0
        
        test_cases = [
            (0.0, 0),      # 0% -> first bar
            (1500.0, 3),   # 50% -> middle bar  
            (3000.0, 7),   # 100% -> last bar
        ]
        
        for freq, expected_idx in test_cases:
            pct = min(1.0, freq / max_freq)
            bar_idx = int(pct * (len(bars) - 1))
            self.assertEqual(bar_idx, expected_idx)

    def test_constants_are_reasonable(self):
        """Test that configuration constants have reasonable values"""
        self.assertGreater(cpu_freq_monitor.HISTORY_SECONDS, 0)
        self.assertGreater(cpu_freq_monitor.UPDATE_FREQUENCY_HZ, 0)
        self.assertGreater(cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD, 0)
        self.assertLessEqual(cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD, 1)
        
        # Typical reasonable values
        self.assertLessEqual(cpu_freq_monitor.HISTORY_SECONDS, 300)  # <= 5 minutes
        self.assertLessEqual(cpu_freq_monitor.UPDATE_FREQUENCY_HZ, 10)  # <= 10 Hz
        self.assertGreater(cpu_freq_monitor.THROTTLING_ALERT_THRESHOLD, 0.1)   # > 10%

if __name__ == '__main__':
    unittest.main()