"""
Configuration constants for the CPU Frequency Monitor.

This module centralizes all configuration settings, thresholds, and display parameters
to make the application easier to configure and maintain.
"""

# ============================================================================
# TIMING AND DISPLAY CONFIGURATION
# ============================================================================

# How many seconds of history to keep for calculating rolling averages
HISTORY_SECONDS = 60

# How many times per second to update the display (1 = once per second)
UPDATE_FREQUENCY_HZ = 1

# ============================================================================
# FREQUENCY MONITORING CONFIGURATION  
# ============================================================================

# Alert threshold: warn if any core's average frequency drops below this
# percentage of the maximum frequency (0.50 = 50%)
THROTTLING_ALERT_THRESHOLD = 0.50

# ============================================================================
# CPU USAGE MONITORING CONFIGURATION
# ============================================================================

# CPU usage thresholds (kept for statistics display, alerts disabled per user feedback)
CPU_USAGE_WARNING_THRESHOLD = 70  # % - warn when core usage exceeds this
CPU_USAGE_HIGH_THRESHOLD = 90     # % - alert when core usage exceeds this

# ============================================================================
# TEMPERATURE MONITORING CONFIGURATION
# ============================================================================

# Temperature alert thresholds
TEMPERATURE_WARNING_THRESHOLD = 80   # °C - warn when core temperature exceeds this
TEMPERATURE_CRITICAL_THRESHOLD = 90  # °C - alert when core temperature exceeds this

# Temperature graph scale (fixed range for consistent visualization)
TEMPERATURE_SCALE_MIN = 40.0  # °C - minimum temperature for graph scale
TEMPERATURE_SCALE_MAX = 100.0 # °C - maximum temperature for graph scale

# ============================================================================
# DISPLAY LAYOUT CONFIGURATION
# ============================================================================

# Layout constants for triple graph display
ROWS_PER_CORE_WITH_TEMPERATURE = 3  # Frequency + Usage + Temperature lines per core

# Unicode block characters for drawing graphs (low to high intensity)
GRAPH_CHARACTERS = '▁▂▃▄▅▆▇█'

# ============================================================================
# TERMINAL COLOR CONFIGURATION
# ============================================================================

# Color pair assignments for terminal display
class Colors:
    """Terminal color pair constants for different UI elements."""
    
    # Graph colors
    FREQUENCY_GRAPH = 1      # Green for frequency graphs
    USAGE_GRAPH = 5          # Cyan for usage graphs  
    TEMPERATURE_GRAPH = 4    # Cyan for temperature graphs
    ALERT_GRAPH = 2          # Red during alert conditions
    
    # Text colors
    NORMAL_TEXT = 6          # Yellow for normal text
    ALERT_TEXT = 4           # White on red for alert text
    
    # Background colors
    NORMAL_BACKGROUND = 0    # Default background
    ALERT_BACKGROUND = 3     # Red background for critical alerts

# ============================================================================
# DERIVED CONFIGURATION
# ============================================================================

def get_temperature_scale_range():
    """Get the temperature scale range in degrees Celsius."""
    return TEMPERATURE_SCALE_MAX - TEMPERATURE_SCALE_MIN

def get_throttling_frequency_threshold(max_frequency):
    """Calculate the frequency threshold for throttling alerts."""
    return max_frequency * THROTTLING_ALERT_THRESHOLD

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values for consistency and sanity."""
    errors = []
    
    # Validate temperature thresholds
    if TEMPERATURE_WARNING_THRESHOLD >= TEMPERATURE_CRITICAL_THRESHOLD:
        errors.append("TEMPERATURE_WARNING_THRESHOLD must be less than TEMPERATURE_CRITICAL_THRESHOLD")
    
    if TEMPERATURE_SCALE_MIN >= TEMPERATURE_SCALE_MAX:
        errors.append("TEMPERATURE_SCALE_MIN must be less than TEMPERATURE_SCALE_MAX")
    
    # Validate usage thresholds
    if CPU_USAGE_WARNING_THRESHOLD >= CPU_USAGE_HIGH_THRESHOLD:
        errors.append("CPU_USAGE_WARNING_THRESHOLD must be less than CPU_USAGE_HIGH_THRESHOLD")
    
    # Validate timing
    if HISTORY_SECONDS <= 0:
        errors.append("HISTORY_SECONDS must be positive")
        
    if UPDATE_FREQUENCY_HZ <= 0:
        errors.append("UPDATE_FREQUENCY_HZ must be positive")
    
    # Validate throttling threshold
    if not 0 < THROTTLING_ALERT_THRESHOLD < 1:
        errors.append("THROTTLING_ALERT_THRESHOLD must be between 0 and 1")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {error}" for error in errors))

# Validate configuration when module is imported
validate_config()