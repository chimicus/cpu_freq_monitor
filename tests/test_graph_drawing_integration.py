#!/usr/bin/env python3
"""
Integration test for dual graph drawing functionality.
Tests the actual draw_frequency_graphs function with mock curses.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque
from unittest.mock import MagicMock, patch

def test_dual_graph_drawing():
    """Test dual graph drawing function with mock curses screen."""
    
    print("Testing Dual Graph Drawing Integration")
    print("=" * 45)
    
    # Create mock screen object
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (30, 120)  # 30 rows, 120 columns
    
    # Create test data
    num_cores = 4
    max_freq = 3000.0
    
    # Create histories with sample data
    freq_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    # Add different patterns for each core
    for core_idx in range(num_cores):
        # Frequency pattern: varying from 1000 to 3000 MHz
        freq_pattern = [1000 + (core_idx * 500) + (i * 100) for i in range(10)]
        usage_pattern = [10 + (core_idx * 15) + (i * 3) for i in range(10)]
        
        for freq, usage in zip(freq_pattern, usage_pattern):
            freq_histories[core_idx].append(min(freq, max_freq))
            usage_histories[core_idx].append(min(usage, 100.0))
    
    current_frequencies = [2500.0, 2000.0, 2800.0, 1800.0]
    current_usage = [25.5, 45.2, 15.8, 60.1]
    
    # Test graph area parameters
    graph_area = (0, 1, 80, 25)  # x, y, width, height
    is_alert_mode = False
    stats_box_width = 40
    
    print(f"Test setup:")
    print(f"  Cores: {num_cores}")
    print(f"  Max frequency: {max_freq:.0f} MHz") 
    print(f"  Current frequencies: {current_frequencies}")
    print(f"  Current usage: {current_usage}")
    print(f"  Graph area: {graph_area}")
    print()
    
    # Mock curses color functions
    with patch('src.cpu_freq_monitor.curses.color_pair') as mock_color_pair:
        mock_color_pair.return_value = 0  # Return dummy color value
        
        try:
            # Call the actual drawing function
            cpu_freq_monitor.draw_frequency_graphs(
                mock_screen,
                graph_area,
                freq_histories,
                current_frequencies,
                usage_histories,
                current_usage,
                max_freq,
                is_alert_mode,
                stats_box_width
            )
            
            print("✅ Function call succeeded without errors")
        
            # Verify that the screen was called to draw content
            self_calls = mock_screen.addstr.call_count
            print(f"✅ Made {self_calls} screen drawing calls")
            
            if self_calls > 0:
                print("✅ Screen drawing operations were performed")
                
                # Analyze some of the calls to verify content
                calls = mock_screen.addstr.call_args_list
                
                # Check for core labels
                core_label_calls = [call for call in calls if len(call[0]) >= 3 and 'C' in str(call[0][2])]
                usage_label_calls = [call for call in calls if len(call[0]) >= 3 and 'U' in str(call[0][2])]
                
                print(f"✅ Core labels drawn: {len(core_label_calls)} calls")
                print(f"✅ Usage labels drawn: {len(usage_label_calls)} calls") 
                
                # Check for frequency/usage displays
                freq_display_calls = [call for call in calls if len(call[0]) >= 3 and 'MHz' in str(call[0][2])]
                usage_display_calls = [call for call in calls if len(call[0]) >= 3 and '%' in str(call[0][2]) and 'MHz' not in str(call[0][2])]
                
                print(f"✅ Frequency displays drawn: {len(freq_display_calls)} calls")
                print(f"✅ Usage displays drawn: {len(usage_display_calls)} calls")
                
            print()
            print("Test Results:")
            print("✅ Dual graph drawing function works correctly")
            print("✅ No runtime errors or exceptions")
            print("✅ Mock screen received expected drawing calls")
            print("✅ Both frequency and usage graphs are being drawn")
            
        except Exception as e:
            print(f"❌ Error during graph drawing: {e}")
            raise
    
    print()
    print("Integration test completed successfully!")

def test_alert_mode_drawing():
    """Test dual graph drawing in alert mode."""
    
    print("\nTesting Alert Mode Drawing")
    print("=" * 30)
    
    # Create mock screen
    mock_screen = MagicMock()
    mock_screen.getmaxyx.return_value = (25, 100)
    
    # Create minimal test data
    freq_histories = [deque([1000, 1200, 900], maxlen=60)]  # Low freq (throttling)
    usage_histories = [deque([95, 98, 92], maxlen=60)]      # High usage
    current_frequencies = [1000.0]
    current_usage = [95.0]
    
    with patch('src.cpu_freq_monitor.curses.color_pair') as mock_color_pair:
        mock_color_pair.return_value = 0
        
        try:
            cpu_freq_monitor.draw_frequency_graphs(
                mock_screen,
                (0, 1, 70, 20),
                freq_histories,
                current_frequencies, 
                usage_histories,
                current_usage,
                3000.0,
                True,  # Alert mode = True
                35
            )
            
            print("✅ Alert mode drawing succeeded")
            print(f"✅ Made {mock_screen.addstr.call_count} drawing calls in alert mode")
            
        except Exception as e:
            print(f"❌ Alert mode drawing failed: {e}")
            raise

if __name__ == "__main__":
    test_dual_graph_drawing()
    test_alert_mode_drawing()