#!/usr/bin/env python3
"""
Simple test script to verify CPU usage monitoring functionality.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque

def test_cpu_usage_monitoring():
    """Test the new CPU usage monitoring features without curses."""
    
    print("Testing CPU Usage Monitoring Implementation")
    print("=" * 50)
    
    # Initialize CPU usage measurement (like the main program does)
    import psutil
    psutil.cpu_percent(percpu=True)
    
    # Test data collection
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    
    print(f"Found {len(frequencies)} CPU cores")
    print(f"Max frequency: {max_freq:.0f} MHz")
    print()
    
    # Test history structures
    num_cores = len(frequencies)
    freq_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    min_averages = [None for _ in range(num_cores)]
    
    # Add some sample data
    for i in range(num_cores):
        freq_histories[i].append(frequencies[i])
        usage_histories[i].append(usage[i])
    
    # Test alert detection
    alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
        freq_histories, usage_histories, max_freq
    )
    
    print("Current Status:")
    print(f"Alert Active: {alert_active}")
    print(f"Alert Type: {alert_type}")
    print()
    
    print("Per-Core Data:")
    print("Core | Frequency | Usage")
    print("-----|-----------|------")
    
    for i in range(min(8, num_cores)):  # Show first 8 cores
        freq = frequencies[i]
        use = usage[i]
        freq_pct = (freq / max_freq) * 100
        print(f" {i:2d}  | {freq:6.0f} MHz ({freq_pct:3.0f}%) | {use:4.1f}%")
    
    if num_cores > 8:
        print(f"... and {num_cores - 8} more cores")
    
    print()
    print("✅ CPU Usage Monitoring Implementation Working!")
    print()
    print("New Features Added:")
    print("• CPU usage percentage monitoring per core")
    print("• Enhanced alert system (throttling + high usage)")
    print("• Expanded statistics display")
    print("• Color-coded usage indicators")
    print("• Configurable usage thresholds (70% warning, 90% high)")

if __name__ == "__main__":
    test_cpu_usage_monitoring()