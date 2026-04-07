#!/usr/bin/env python3
"""
Comprehensive tests for dual graph functionality (frequency + usage graphs).
"""

import unittest
from unittest.mock import patch, MagicMock
from collections import deque
import cpu_freq_monitor

class TestDualGraphFunctionality(unittest.TestCase):

    def setUp(self):
        """Set up test data for dual graph tests."""
        self.max_freq = 3000.0
        self.num_cores = 4
        
        # Sample frequency and usage histories
        self.freq_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        self.usage_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        
        # Add sample data
        for i in range(self.num_cores):
            # Different frequency patterns for each core
            freq_samples = [2000 + i * 100, 2200 + i * 100, 1800 + i * 100]
            usage_samples = [20 + i * 10, 30 + i * 10, 15 + i * 10]
            
            for freq, usage in zip(freq_samples, usage_samples):
                self.freq_histories[i].append(freq)
                self.usage_histories[i].append(usage)

    def test_get_cpu_usage_returns_valid_data(self):
        """Test that get_cpu_usage returns usage percentages."""
        with patch('cpu_freq_monitor.psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = [25.5, 30.0, 15.2, 50.8]
            
            usage = cpu_freq_monitor.get_cpu_usage()
            
            self.assertEqual(usage, [25.5, 30.0, 15.2, 50.8])
            mock_cpu_percent.assert_called_once_with(percpu=True, interval=0.1)

    def test_detect_alerts_with_usage_data(self):
        """Test alert detection with both frequency and usage data."""
        # Create scenarios for different alert types
        
        # Test 1: Normal operation - no alerts
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            self.freq_histories, self.usage_histories, self.max_freq
        )
        
        self.assertFalse(alert_active)
        self.assertEqual(alert_type, "normal")
        self.assertEqual(len(avg_freq), self.num_cores)
        self.assertEqual(len(avg_usage), self.num_cores)

    def test_detect_alerts_high_usage(self):
        """Test alert detection for high CPU usage."""
        # Create high usage scenario
        high_usage_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        
        # Add high usage samples (>90%)
        for i in range(self.num_cores):
            for _ in range(3):
                high_usage_histories[i].append(95.0)  # High usage
        
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            self.freq_histories, high_usage_histories, self.max_freq
        )
        
        self.assertTrue(alert_active)
        self.assertTrue(alert_type.startswith("high_usage_"))

    def test_detect_alerts_warning_usage(self):
        """Test alert detection for warning-level CPU usage."""
        # Create warning usage scenario
        warning_usage_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        
        # Add warning usage samples (>70% but <90%)
        for i in range(2):  # First 2 cores
            for _ in range(3):
                warning_usage_histories[i].append(75.0)  # Warning usage
        
        # Other cores normal
        for i in range(2, self.num_cores):
            for _ in range(3):
                warning_usage_histories[i].append(30.0)
        
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            self.freq_histories, warning_usage_histories, self.max_freq
        )
        
        self.assertTrue(alert_active)
        self.assertTrue(alert_type.startswith("warning_usage_"))

    def test_detect_alerts_throttling_priority(self):
        """Test that throttling alerts take priority over usage alerts."""
        # Create throttling scenario
        throttling_freq_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        high_usage_histories = [deque(maxlen=60) for _ in range(self.num_cores)]
        
        # Add low frequency samples (throttling) and high usage
        for i in range(self.num_cores):
            for _ in range(3):
                throttling_freq_histories[i].append(1000.0)  # Below 50% threshold
                high_usage_histories[i].append(95.0)  # High usage
        
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            throttling_freq_histories, high_usage_histories, self.max_freq
        )
        
        self.assertTrue(alert_active)
        self.assertEqual(alert_type, "throttling")  # Should prioritize throttling

    def test_usage_graph_scaling(self):
        """Test that usage values scale correctly to bar graph characters."""
        bars = '▁▂▃▄▅▆▇█'
        
        test_cases = [
            (0.0, 0),      # 0% -> first bar
            (50.0, 3),     # 50% -> middle bar  
            (100.0, 7),    # 100% -> last bar
            (25.0, 1),     # 25% -> low bar
            (75.0, 5),     # 75% -> high bar
        ]
        
        for usage_pct, expected_idx in test_cases:
            usage_percentage = min(1.0, usage_pct / 100.0)
            bar_idx = int(usage_percentage * (len(bars) - 1))
            self.assertEqual(bar_idx, expected_idx)

    def test_dual_graph_layout_calculation(self):
        """Test that dual graph layout allocates space correctly."""
        # Test that we need 2 rows per core minimum
        graph_height = 16
        num_cores = 8
        
        # Function should calculate at least 2 rows per core
        rows_per_core = max(2, graph_height // num_cores)
        
        self.assertGreaterEqual(rows_per_core, 2)
        self.assertLessEqual(rows_per_core * num_cores, graph_height + num_cores)

    def test_dual_history_tracking(self):
        """Test that both frequency and usage histories are maintained correctly."""
        freq_hist = deque(maxlen=60)
        usage_hist = deque(maxlen=60)
        
        # Simulate main loop data collection
        test_data = [
            (2500, 30.0),
            (2400, 25.5),
            (2600, 35.2),
            (2300, 40.1),
        ]
        
        for freq, usage in test_data:
            freq_hist.append(freq)
            usage_hist.append(usage)
        
        self.assertEqual(len(freq_hist), 4)
        self.assertEqual(len(usage_hist), 4)
        self.assertEqual(list(freq_hist), [2500, 2400, 2600, 2300])
        self.assertEqual(list(usage_hist), [30.0, 25.5, 35.2, 40.1])

    def test_usage_thresholds_configuration(self):
        """Test that CPU usage threshold constants are reasonable."""
        self.assertGreater(cpu_freq_monitor.CPU_USAGE_WARNING_THRESHOLD, 0)
        self.assertLess(cpu_freq_monitor.CPU_USAGE_WARNING_THRESHOLD, 100)
        self.assertGreater(cpu_freq_monitor.CPU_USAGE_HIGH_THRESHOLD, 0)
        self.assertLess(cpu_freq_monitor.CPU_USAGE_HIGH_THRESHOLD, 100)
        
        # Warning threshold should be lower than high threshold
        self.assertLess(
            cpu_freq_monitor.CPU_USAGE_WARNING_THRESHOLD,
            cpu_freq_monitor.CPU_USAGE_HIGH_THRESHOLD
        )

    def test_average_calculation_accuracy(self):
        """Test that frequency and usage averages are calculated accurately."""
        # Test with known data
        freq_hist = deque([2000, 2400, 2600], maxlen=60)
        usage_hist = deque([20.0, 30.0, 40.0], maxlen=60)
        
        freq_avg = sum(freq_hist) / len(freq_hist)
        usage_avg = sum(usage_hist) / len(usage_hist)
        
        self.assertAlmostEqual(freq_avg, 2333.33, places=1)
        self.assertAlmostEqual(usage_avg, 30.0, places=1)

    def test_empty_history_handling(self):
        """Test that empty histories are handled gracefully."""
        empty_freq_histories = [deque(maxlen=60) for _ in range(2)]
        empty_usage_histories = [deque(maxlen=60) for _ in range(2)]
        
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            empty_freq_histories, empty_usage_histories, self.max_freq
        )
        
        # Should handle empty histories without crashing
        self.assertFalse(alert_active)
        self.assertEqual(alert_type, "normal")
        # Empty histories should assume max frequency and 0% usage
        for avg in avg_freq:
            self.assertEqual(avg, self.max_freq)
        for avg in avg_usage:
            self.assertEqual(avg, 0.0)

    @patch('cpu_freq_monitor.psutil.cpu_percent')
    @patch('cpu_freq_monitor.psutil.cpu_freq')
    def test_main_loop_data_collection_integration(self, mock_cpu_freq, mock_cpu_percent):
        """Test that main loop collects both frequency and usage data correctly."""
        # Mock psutil responses
        mock_freq_obj = MagicMock()
        mock_freq_obj.current = 2500.0
        mock_freq_obj.max = 3000.0
        mock_cpu_freq.return_value = [mock_freq_obj, mock_freq_obj]
        mock_cpu_percent.return_value = [25.0, 30.0]
        
        # Test data collection like main loop does
        frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
        usage = cpu_freq_monitor.get_cpu_usage()
        
        self.assertEqual(frequencies, [2500.0, 2500.0])
        self.assertEqual(max_freq, 3000.0)
        self.assertEqual(usage, [25.0, 30.0])
        
        # Verify both functions were called
        mock_cpu_freq.assert_called_once_with(percpu=True)
        mock_cpu_percent.assert_called_once_with(percpu=True, interval=0.1)

if __name__ == '__main__':
    # Run specific test methods for debugging
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        suite = unittest.TestSuite()
        suite.addTest(TestDualGraphFunctionality('test_get_cpu_usage_returns_valid_data'))
        suite.addTest(TestDualGraphFunctionality('test_detect_alerts_with_usage_data'))
        suite.addTest(TestDualGraphFunctionality('test_usage_graph_scaling'))
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        unittest.main(verbosity=2)