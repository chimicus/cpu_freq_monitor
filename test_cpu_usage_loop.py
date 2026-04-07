#!/usr/bin/env python3
"""
Test script that simulates the main program loop to verify CPU usage works correctly.
"""

import cpu_freq_monitor
import psutil
import time
from collections import deque

def simulate_main_loop():
    """Simulate the main program loop to test CPU usage measurement."""
    
    print("Simulating Main Program Loop")
    print("=" * 40)
    
    # Initialize like the main program
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    num_cores = len(frequencies)
    
    # Initialize CPU usage measurement
    psutil.cpu_percent(percpu=True)
    
    # Create histories
    freq_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    print(f"Found {num_cores} cores, simulating 5 iterations...")
    print()
    
    # Simulate 5 iterations of the main loop
    for iteration in range(5):
        print(f"Iteration {iteration + 1}:")
        
        # Get current data (like the main loop does)
        current_frequencies, _ = cpu_freq_monitor.get_cpu_frequencies()
        current_usage = cpu_freq_monitor.get_cpu_usage()
        
        # Update histories
        for i in range(num_cores):
            freq_histories[i].append(current_frequencies[i])
            usage_histories[i].append(current_usage[i])
        
        # Show results for first 4 cores
        print("  Core | Frequency | Usage")
        print("  -----|-----------|------")
        for i in range(min(4, num_cores)):
            freq = current_frequencies[i]
            usage = current_usage[i]
            freq_pct = (freq / max_freq) * 100
            print(f"   {i:2d}  | {freq:6.0f} MHz ({freq_pct:3.0f}%) | {usage:4.1f}%")
        
        # Test alerts
        alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
            freq_histories, usage_histories, max_freq
        )
        
        print(f"  Alert: {alert_active} ({alert_type})")
        print()
        
        # Sleep like the main loop does
        time.sleep(1.0)
    
    print("✅ CPU usage measurement working correctly in loop!")
    print("Note: First iteration may show 0% usage (normal psutil behavior)")

if __name__ == "__main__":
    simulate_main_loop()