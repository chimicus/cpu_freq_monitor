#!/usr/bin/env python3
"""
Debug why the red background is appearing.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque

def debug_red_background():
    """Simulate the main loop logic to debug red background."""
    
    print("Debugging Red Background Issue")
    print("=" * 35)
    
    # Get current data like main loop does
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    temperatures = cpu_freq_monitor.get_cpu_temperatures()
    
    num_cores = len(frequencies)
    
    print(f"Data collected:")
    print(f"  Cores: {num_cores}")
    print(f"  Max frequency: {max_freq:.0f} MHz")
    print(f"  Temperatures available: {len(temperatures) if temperatures else 'None'}")
    print()
    
    # Create histories like main loop does
    frequency_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]  
    temperature_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    # Add data like main loop does
    for core_index, current_frequency in enumerate(frequencies):
        frequency_histories[core_index].append(current_frequency)
        usage_histories[core_index].append(usage[core_index])
        
        # Add temperature data if available
        if temperatures and core_index < len(temperatures):
            temperature_histories[core_index].append(temperatures[core_index])
    
    print("After adding data to histories:")
    print(f"  Frequency histories lengths: {[len(h) for h in frequency_histories]}")
    print(f"  Temperature histories lengths: {[len(h) for h in temperature_histories]}")
    print()
    
    # Check alert detection like main loop does
    alert_active, alert_type, average_frequencies, average_usage = cpu_freq_monitor.detect_alerts(
        frequency_histories, usage_histories, max_freq
    )
    
    print(f"Alert detection results:")
    print(f"  Alert active: {alert_active}")
    print(f"  Alert type: {alert_type}")
    print()
    
    # Calculate temperature averages like main loop does
    average_temperatures = None
    if any(len(temp_hist) > 0 for temp_hist in temperature_histories):
        average_temperatures = []
        for temp_history in temperature_histories:
            if len(temp_history) > 0:
                avg_temp = sum(temp_history) / len(temp_history)
                average_temperatures.append(avg_temp)
            else:
                average_temperatures.append(None)
    
    print(f"Temperature averages:")
    if average_temperatures:
        for i, temp in enumerate(average_temperatures):
            if temp is not None:
                print(f"  Core {i}: {temp:.1f}°C")
            else:
                print(f"  Core {i}: None")
    else:
        print("  None calculated")
    print()
    
    # Check critical alert conditions like main loop does
    critical_alert = False
    
    # Check for throttling
    if alert_type == "throttling":
        critical_alert = True
        print("🔥 Critical alert: THROTTLING detected")
    
    # Check for critical temperature
    if average_temperatures:
        for i, temp in enumerate(average_temperatures):
            if temp is not None and temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                critical_alert = True
                print(f"🔥 Critical alert: Core {i} temperature {temp:.1f}°C >= {cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD}°C")
                break
    
    print(f"Final critical_alert status: {critical_alert}")
    print(f"Red background would be: {'ACTIVE' if critical_alert else 'INACTIVE'}")

if __name__ == "__main__":
    debug_red_background()