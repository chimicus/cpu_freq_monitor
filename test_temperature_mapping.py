#!/usr/bin/env python3
"""
Test the new temperature mapping from physical to logical cores.
"""

import psutil
import cpu_freq_monitor

def test_temperature_mapping():
    """Debug the temperature mapping functionality."""
    
    print("Testing Temperature Mapping (Physical → Logical Cores)")
    print("=" * 55)
    
    # Check CPU configuration
    logical_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)
    print(f"System CPU Configuration:")
    print(f"  Logical cores: {logical_cores}")
    print(f"  Physical cores: {physical_cores}")
    print(f"  Hyperthreading ratio: {logical_cores // physical_cores if physical_cores else 'N/A'}")
    print()
    
    # Check raw sensor data
    print("Raw Sensor Data:")
    try:
        sensors = psutil.sensors_temperatures()
        if sensors:
            for sensor_name, sensor_list in sensors.items():
                print(f"  {sensor_name}:")
                for sensor in sensor_list:
                    print(f"    {sensor.label}: {sensor.current}°C")
        else:
            print("  No sensors found")
    except Exception as e:
        print(f"  Error reading sensors: {e}")
    print()
    
    # Test our new function
    print("Our Temperature Function Results:")
    try:
        temps = cpu_freq_monitor.get_cpu_temperatures()
        if temps:
            print(f"  Found {len(temps)} temperature readings:")
            for i, temp in enumerate(temps):
                if temp is not None:
                    print(f"    Logical core {i}: {temp:.1f}°C")
                else:
                    print(f"    Logical core {i}: N/A")
        else:
            print("  No temperature data returned")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Show expected mapping
    print("Expected Mapping (for hyperthreaded systems):")
    if physical_cores and logical_cores:
        cores_per_physical = logical_cores // physical_cores
        for logical_core in range(logical_cores):
            physical_core = logical_core // cores_per_physical
            print(f"  Logical core {logical_core} ← Physical core {physical_core}")

if __name__ == "__main__":
    test_temperature_mapping()