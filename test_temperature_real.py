#!/usr/bin/env python3
"""
Real-world test of temperature reading functionality.
"""

import cpu_freq_monitor

def test_real_temperature_reading():
    """Test temperature reading with actual system sensors."""
    
    print("Testing Real Temperature Reading")
    print("=" * 35)
    
    # Test that constants are properly defined
    print("Temperature Thresholds:")
    print(f"  Warning: {cpu_freq_monitor.TEMPERATURE_WARNING_THRESHOLD}°C")
    print(f"  Critical: {cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD}°C")
    print()
    
    # Try to read actual temperatures
    print("Reading CPU temperatures...")
    temps = cpu_freq_monitor.get_cpu_temperatures()
    
    if temps is None:
        print("❌ No temperature sensors available on this system")
        print("This is normal on some systems (VMs, limited hardware access)")
        return
    
    print(f"✅ Found {len(temps)} temperature readings:")
    for i, temp in enumerate(temps):
        status = ""
        if temp >= cpu_freq_monitor.TEMPERATURE_CRITICAL_THRESHOLD:
            status = " 🔥 CRITICAL"
        elif temp >= cpu_freq_monitor.TEMPERATURE_WARNING_THRESHOLD:
            status = " ⚠️  WARNING"
        else:
            status = " ✅ NORMAL"
        
        print(f"  Core {i}: {temp:.1f}°C{status}")
    
    print()
    print("Integration test:")
    
    # Test alongside existing functions
    try:
        frequencies, max_freq = cpu_freq_monitor.get_cpu_frequencies()
        usage = cpu_freq_monitor.get_cpu_usage()
        temps = cpu_freq_monitor.get_cpu_temperatures()
        
        print(f"✅ Frequencies: {len(frequencies)} cores")
        print(f"✅ Usage: {len(usage)} cores") 
        print(f"✅ Temperatures: {len(temps) if temps else 'None'} cores")
        
        print()
        print("All three metrics working together:")
        for i in range(min(4, len(frequencies))):  # Show first 4 cores
            freq_pct = (frequencies[i] / max_freq) * 100
            temp_str = f"{temps[i]:.1f}°C" if temps and i < len(temps) else "N/A"
            print(f"  Core {i}: {frequencies[i]:>4.0f} MHz ({freq_pct:>3.0f}%) | {usage[i]:>5.1f}% | {temp_str}")
        
    except Exception as e:
        print(f"❌ Error during integration test: {e}")

if __name__ == "__main__":
    test_real_temperature_reading()