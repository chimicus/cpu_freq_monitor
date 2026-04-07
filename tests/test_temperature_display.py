#!/usr/bin/env python3
"""
Test temperature display in the statistics table.
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
from collections import deque

def test_temperature_in_statistics():
    """Test that temperature data is properly displayed in the statistics table."""
    
    print("Testing Temperature Display in Statistics Table")
    print("=" * 48)
    
    # Get real data
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    temperatures = cpu_freq_monitor.get_cpu_temperatures()
    
    num_cores = len(frequencies)
    print(f"System: {num_cores} cores, max freq: {max_freq:.0f} MHz")
    
    if temperatures:
        print(f"Temperature sensors: {len(temperatures)} readings")
    else:
        print("Temperature sensors: Not available")
    
    print()
    
    # Create histories like the main application
    freq_histories = [deque([f], maxlen=60) for f in frequencies]
    usage_histories = [deque([u], maxlen=60) for u in usage]
    temp_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    # Add temperature data if available
    if temperatures:
        for i, temp in enumerate(temperatures):
            if i < len(temp_histories):
                temp_histories[i].append(temp)
    
    # Calculate averages like the main loop does
    alert_active, alert_type, avg_freq, avg_usage = cpu_freq_monitor.detect_alerts(
        freq_histories, usage_histories, max_freq
    )
    
    # Calculate temperature averages
    avg_temperatures = None
    if any(len(temp_hist) > 0 for temp_hist in temp_histories):
        avg_temperatures = []
        for temp_history in temp_histories:
            if len(temp_history) > 0:
                avg_temp = sum(temp_history) / len(temp_history)
                avg_temperatures.append(avg_temp)
            else:
                avg_temperatures.append(None)
    
    print("Statistics Table Format:")
    print(" Core  Freq  %  Usage%  Temp  Min%")
    print("------|-----|---|-------|------|----")
    
    min_averages = [None for _ in range(num_cores)]
    
    for i in range(min(6, num_cores)):  # Show first 6 cores
        freq_pct = (avg_freq[i] / max_freq) * 100
        usage_pct = avg_usage[i]
        
        if avg_temperatures and i < len(avg_temperatures) and avg_temperatures[i] is not None:
            temp_str = f"{avg_temperatures[i]:>3.0f}°C"
        else:
            temp_str = " N/A "
        
        min_pct_str = "---"
        
        print(f"  {i:2d}  {avg_freq[i]:>4.0f} {freq_pct:>2.0f}% {usage_pct:>5.1f}% {temp_str} {min_pct_str}")
    
    if num_cores > 6:
        print(f"... and {num_cores - 6} more cores")
    
    print()
    print("Temperature Status Check:")
    if avg_temperatures:
        for i, temp in enumerate(avg_temperatures):
            if temp is not None:
                status = "NORMAL"
                if temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
                    status = "🔥 CRITICAL"
                elif temp >= cpu_freq_monitor.TEMPERATURE_WARNING_THRESHOLD:
                    status = "⚠️  WARNING"
                else:
                    status = "✅ NORMAL"
                print(f"  Core {i}: {temp:.1f}°C - {status}")
    else:
        print("  No temperature data available")
    
    print()
    print("✅ Temperature display integration test completed!")

if __name__ == "__main__":
    test_temperature_in_statistics()