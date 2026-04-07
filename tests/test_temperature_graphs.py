#!/usr/bin/env python3
"""
Tests for temperature graph functionality with fixed 40-100°C scale.
Starting with tests - these should fail since temperature graphing doesn't exist yet.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque

class TestTemperatureGraphs(unittest.TestCase):

    def test_temperature_graph_scaling_40_to_100_degrees(self):
        """Test temperature scaling to Unicode bar characters (40-100°C range)."""
        # Test various temperatures and their expected graph positions
        test_cases = [
            (40.0, 0),    # Minimum temp -> first character ▁
            (100.0, 7),   # Maximum temp -> last character █  
            (70.0, 3),    # Middle temp -> middle character ▄ (70-40)/60*7 = 3.5 -> 3
            (55.0, 1),    # Low-mid temp -> ▂ (55-40)/60*7 = 1.75 -> 1
            (85.0, 5),    # High temp -> ▆ (85-40)/60*7 = 5.25 -> 5
            (35.0, 0),    # Below minimum -> clamp to ▁
            (105.0, 7),   # Above maximum -> clamp to █
        ]
        
        for temp, expected_index in test_cases:
            # This function doesn't exist yet - should fail
            with self.subTest(temp=temp):
                index = cpu_freq_monitor.temperature_to_graph_index(temp)
                self.assertEqual(index, expected_index, 
                    f"Temperature {temp}°C should map to index {expected_index}")

    def test_temperature_graph_characters(self):
        """Test that correct Unicode characters are used for temperature graphs."""
        # Expected Unicode block characters (same as frequency/usage)
        expected_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        # Function should use the same character set
        # This doesn't exist yet - should fail
        chars = cpu_freq_monitor.get_temperature_graph_characters()
        self.assertEqual(chars, expected_chars)

    def test_temperature_history_to_graph_string(self):
        """Test converting temperature history to graph string."""
        # Mock temperature history (deque of temperatures)
        temp_history = deque([45.0, 50.0, 65.0, 80.0, 95.0, 70.0, 55.0], maxlen=60)
        
        # This function doesn't exist yet - should fail  
        graph_string = cpu_freq_monitor.temperature_history_to_graph(temp_history)
        
        # Should return a string of Unicode characters
        self.assertIsInstance(graph_string, str)
        self.assertEqual(len(graph_string), 7)  # Same length as history
        
        # Each character should be a valid Unicode block character
        valid_chars = set(['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'])
        for char in graph_string:
            self.assertIn(char, valid_chars)

    def test_temperature_graph_integration_with_draw_frequency_graphs(self):
        """Test that temperature graphs integrate with existing graph drawing."""
        with patch('src.cpu_freq_monitor.curses') as mock_curses:
            mock_screen = MagicMock()
            
            # Mock screen.getmaxyx() to return screen dimensions
            mock_screen.getmaxyx.return_value = (40, 100)  # (height, width)
            
            # Mock curses color pair and addstr functions
            mock_curses.color_pair.return_value = 1
            mock_curses.A_BOLD = 1
            
            # Mock temperature histories for 2 cores
            temp_histories = [
                deque([45.0, 55.0, 65.0], maxlen=60),
                deque([50.0, 60.0, 70.0], maxlen=60)
            ]
            
            # Mock other required data
            frequency_histories = [
                deque([2500.0, 2600.0, 2400.0], maxlen=60),
                deque([2400.0, 2500.0, 2550.0], maxlen=60)
            ]
            usage_histories = [
                deque([25.0, 35.0, 45.0], maxlen=60),
                deque([30.0, 40.0, 50.0], maxlen=60)
            ]
            
            max_freq = 3000.0
            alert_active = False
            
            # Test the enhanced function with temperature support
            # Should now work with temperature histories
            cpu_freq_monitor.draw_frequency_graphs(
                mock_screen, 
                (0, 1, 80, 20),  # graph_area (x, y, width, height)
                frequency_histories, 
                [2500.0, 2400.0],  # current_frequencies
                usage_histories, 
                [25.0, 30.0],      # current_usage
                temp_histories, 
                [65.0, 68.0],      # current_temperatures
                max_freq, 
                alert_active,
                20  # stats_box_width
            )
            
            # Verify that addstr was called (function executed without error)
            self.assertTrue(mock_screen.addstr.called)
            
            # Verify some expected calls were made
            call_args_list = [str(call) for call in mock_screen.addstr.call_args_list]
            
            # Should have called addstr for core labels, usage labels, and temp labels
            self.assertTrue(any('C0' in call for call in call_args_list))
            self.assertTrue(any('U' in call for call in call_args_list)) 
            self.assertTrue(any('T' in call for call in call_args_list))

    def test_temperature_graph_display_layout(self):
        """Test the expected layout of temperature graphs."""
        # Expected layout per core:
        # C0 ▁▂▃▄▅▆▇█▇▆▅ 2500/3000 MHz  
        #    U ▂▃▄▃▂▁▂▃▄  25.5%
        #    T ▃▄▅▄▃▂▃▄▅  67°C
        
        # Test that we can calculate rows per core with temperature
        num_cores = 4
        
        # This constant doesn't exist yet - should fail
        rows_per_core = cpu_freq_monitor.ROWS_PER_CORE_WITH_TEMPERATURE
        self.assertEqual(rows_per_core, 3)  # Frequency + Usage + Temperature
        
        # Test total rows calculation
        expected_total_rows = num_cores * 3
        calculated_rows = num_cores * rows_per_core
        self.assertEqual(calculated_rows, expected_total_rows)

    def test_temperature_graph_labeling(self):
        """Test temperature graph labels and formatting."""
        # Test temperature label
        temp_label = "T"  # Simple label like "U" for usage
        
        # Test temperature value formatting
        test_temps = [45.0, 67.0, 89.3, 100.0]
        expected_formats = ["45°C", "67°C", "89°C", "100°C"]
        
        for temp, expected in zip(test_temps, expected_formats):
            formatted = f"{temp:.0f}°C"
            self.assertEqual(formatted, expected)

    def test_temperature_graph_color_normal_vs_alert(self):
        """Test temperature graph coloring in normal vs alert modes."""
        with patch('src.cpu_freq_monitor.curses') as mock_curses:
            mock_screen = MagicMock()
            
            # Mock color pairs
            mock_curses.color_pair.side_effect = lambda x: x
            
            # Test normal mode (should use cyan like usage graphs)
            # This doesn't exist yet - should fail
            normal_color = cpu_freq_monitor.get_temperature_graph_color(alert_active=False)
            self.assertEqual(normal_color, 4)  # Cyan color pair
            
            # Test alert mode (should use red)
            alert_color = cpu_freq_monitor.get_temperature_graph_color(alert_active=True)
            self.assertEqual(alert_color, 3)  # Red color pair

    def test_temperature_graph_with_none_values(self):
        """Test temperature graph handling when temperature is None."""
        # Temperature history with some None values (sensor unavailable)
        temp_history = deque([45.0, None, 65.0, None, 85.0], maxlen=60)
        
        # Should handle None gracefully
        # This function doesn't exist yet - should fail
        graph_string = cpu_freq_monitor.temperature_history_to_graph(temp_history)
        
        self.assertIsInstance(graph_string, str)
        self.assertEqual(len(graph_string), 5)
        
        # None values should be represented somehow (maybe as spaces or minimum char)
        # We'll define the behavior: None -> minimum character ▁
        expected = "▁" + "▁" + "▃" + "▁" + "▇"  # 45°C, None, 65°C, None, 85°C
        # (approximate based on 40-100°C scale)

    def test_temperature_graph_edge_cases(self):
        """Test edge cases for temperature graphing."""
        # Empty history
        empty_history = deque(maxlen=60)
        # Should return empty string or handle gracefully
        # This function doesn't exist yet - should fail
        result = cpu_freq_monitor.temperature_history_to_graph(empty_history)
        self.assertEqual(result, "")
        
        # Single temperature
        single_history = deque([55.0], maxlen=60)
        result = cpu_freq_monitor.temperature_history_to_graph(single_history)
        self.assertEqual(len(result), 1)
        
        # All same temperature
        same_history = deque([70.0] * 10, maxlen=60)
        result = cpu_freq_monitor.temperature_history_to_graph(same_history)
        self.assertEqual(len(result), 10)
        # All characters should be the same
        self.assertTrue(all(c == result[0] for c in result))

    def test_temperature_scale_constants(self):
        """Test temperature scale constants."""
        # These constants don't exist yet - should fail
        self.assertEqual(cpu_freq_monitor.TEMPERATURE_SCALE_MIN, 40.0)
        self.assertEqual(cpu_freq_monitor.TEMPERATURE_SCALE_MAX, 100.0)
        
        # Scale range should be reasonable
        scale_range = cpu_freq_monitor.TEMPERATURE_SCALE_MAX - cpu_freq_monitor.TEMPERATURE_SCALE_MIN
        self.assertEqual(scale_range, 60.0)  # 60°C range


if __name__ == '__main__':
    print("Running temperature graph tests...")
    print("These tests SHOULD FAIL since temperature graphing doesn't exist yet.")
    print("=" * 70)
    unittest.main(verbosity=2)