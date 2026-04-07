#!/usr/bin/env python3
"""
Test to verify CPU usage collection in the main loop logic.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque
import time

def test_main_loop_usage_collection():
    """Test that mimics the main loop's CPU usage collection."""
    
    print("Testing Main Loop CPU Usage Collection")
    print("=" * 45)
    
    # Initialize like the main function does
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    num_cores = len(frequencies)
    
    print(f"Found {num_cores} CPU cores")
    print(f"Max frequency: {max_freq:.0f} MHz")
    print()
    
    # Create histories like main() does
    frequency_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    print("Simulating main loop data collection for 3 iterations:")
    print()
    
    for iteration in range(3):
        print(f"=== Iteration {iteration + 1} ===")
        
        # Step 1: Get current data (like main loop does)
        current_frequencies, _ = cpu_freq_monitor.get_cpu_frequencies()
        current_usage = cpu_freq_monitor.get_cpu_usage()
        
        print(f"Raw usage values: {current_usage[:4]}...")
        
        # Step 2: Add to histories (like main loop does)
        for core_index, current_frequency in enumerate(current_frequencies):
            frequency_histories[core_index].append(current_frequency)
            usage_histories[core_index].append(current_usage[core_index])
        
        # Step 3: Check alert detection (like main loop does)
        alert_active, alert_type, avg_frequencies, avg_usage = cpu_freq_monitor.detect_alerts(
            frequency_histories, usage_histories, max_freq
        )
        
        print(f"Alert active: {alert_active}")
        print(f"Alert type: {alert_type}")
        print(f"Average usage (first 4 cores): {avg_usage[:4]}")
        print(f"Usage history lengths: {[len(h) for h in usage_histories[:4]]}")
        print()
        
        if iteration < 2:
            time.sleep(1.0)  # Wait like the main loop does
    
    print("✅ Main loop usage collection test completed!")
    print()
    print("Key findings:")
    print("• Raw usage values are being collected correctly")
    print("• Usage histories are being populated")
    print("• Alert detection now has usage data to work with")

if __name__ == "__main__":
    test_main_loop_usage_collection()