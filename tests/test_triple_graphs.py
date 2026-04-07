#!/usr/bin/env python3
"""
Functional test for triple graph display (frequency + usage + temperature).
"""

import sys; sys.path.insert(0, "."); from src import cpu_freq_monitor
import time
from collections import deque

def test_triple_graph_functionality():
    """Test the triple graph functionality with real data."""
    
    print("Testing Triple Graph Functionality (Frequency + Usage + Temperature)")
    print("=" * 70)
    
    # Get real system data
    frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
    usage = cpu_freq_monitor.get_cpu_usage()
    temperatures = cpu_freq_monitor.get_cpu_temperatures()
    
    num_cores = len(frequencies)
    print(f"System: {num_cores} cores, max frequency: {max_freq:.0f} MHz")
    
    if temperatures:
        temp_count = sum(1 for t in temperatures if t is not None)
        print(f"Temperature sensors: {temp_count}/{len(temperatures)} cores available")
    else:
        print("Temperature sensors: Not available")
    print()
    
    # Create histories like the main application
    frequency_histories = [deque(maxlen=60) for _ in range(num_cores)]
    usage_histories = [deque(maxlen=60) for _ in range(num_cores)]
    temperature_histories = [deque(maxlen=60) for _ in range(num_cores)]
    
    # Collect data for a few iterations
    print("Collecting data for triple graph display...")
    for iteration in range(5):
        print(f"  Data collection {iteration + 1}/5...")
        
        # Get fresh data
        frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
        usage = cpu_freq_monitor.get_cpu_usage()
        temperatures = cpu_freq_monitor.get_cpu_temperatures()
        
        # Add to histories
        for core_index in range(num_cores):
            frequency_histories[core_index].append(frequencies[core_index])
            usage_histories[core_index].append(usage[core_index])
            
            # Add temperature data
            if temperatures and core_index < len(temperatures):
                temp_value = temperatures[core_index]
                temperature_histories[core_index].append(temp_value)
            else:
                temperature_histories[core_index].append(None)
        
        time.sleep(0.5)  # Short delay between collections
    
    print()
    print("Sample Data Collected:")
    print("Core | Frequency | Usage | Temperature")
    print("-----|-----------|-------|-------------")
    
    for i in range(min(4, num_cores)):  # Show first 4 cores
        freq_hist = list(frequency_histories[i])
        usage_hist = list(usage_histories[i])
        temp_hist = list(temperature_histories[i])
        
        if freq_hist:
            avg_freq = sum(freq_hist) / len(freq_hist)
            avg_usage = sum(usage_hist) / len(usage_hist)
            
            if temp_hist and any(t is not None for t in temp_hist):
                valid_temps = [t for t in temp_hist if t is not None]
                avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else None
                temp_str = f"{avg_temp:.1f}°C" if avg_temp else "N/A"
            else:
                temp_str = "N/A"
            
            print(f"  {i:2d} | {avg_freq:>8.0f} | {avg_usage:>4.1f}% | {temp_str:>8s}")
    
    if num_cores > 4:
        print(f"... and {num_cores - 4} more cores")
    
    print()
    print("Expected Triple Graph Layout (per core):")
    print("C0 ▁▂▃▄▅▆▇█▇▆▅ 2500/3000 MHz")
    print("   U ▂▃▄▃▂▁▂▃▄  25.5%")
    print("   T ▃▄▅▄▃▂▃▄▅  67°C")
    print()
    
    # Test temperature scale calculations  
    if temperatures and any(t is not None for t in temperatures):
        valid_temps = [t for t in temperatures if t is not None]
        min_temp = min(valid_temps)
        max_temp = max(valid_temps)
        
        print(f"Current Temperature Range: {min_temp:.1f}°C to {max_temp:.1f}°C")
        print(f"Fixed Scale Range: 40.0°C to 100.0°C (60°C span)")
        
        # Show how current temps would map to scale
        print("\nTemperature Mapping Examples:")
        for temp in valid_temps[:4]:  # First 4 temperatures
            # This calculation doesn't exist yet but shows expected behavior
            scale_position = max(0, min(100, ((temp - 40.0) / 60.0) * 100))
            graph_index = int(scale_position / 100 * 7)  # 0-7 for Unicode chars
            chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
            char = chars[graph_index]
            print(f"  {temp:.1f}°C → {scale_position:.1f}% → {char}")
    
    print()
    print("✅ Triple graph functionality test completed!")
    print("Next: Implement temperature graphing functions and integration")

if __name__ == "__main__":
    test_triple_graph_functionality()