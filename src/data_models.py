"""
Data models for CPU monitoring metrics and system state.

This module defines the core data structures that represent CPU metrics,
system state, and display parameters in a clean, object-oriented way.
"""

from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Deque
from src import config


@dataclass
class MetricPoint:
    """A single measurement point for a CPU metric."""
    value: Optional[float]
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Validate the metric point after initialization."""
        if self.value is not None and self.value < 0:
            raise ValueError("Metric values cannot be negative")


class CoreMetrics:
    """Manages all metrics for a single CPU core."""
    
    def __init__(self, core_id: int):
        self.core_id = core_id
        
        # Rolling history for each metric type
        self.frequency_history: Deque[float] = deque(maxlen=config.HISTORY_SECONDS)
        self.usage_history: Deque[float] = deque(maxlen=config.HISTORY_SECONDS)
        self.temperature_history: Deque[Optional[float]] = deque(maxlen=config.HISTORY_SECONDS)
        
        # Current values
        self.current_frequency: float = 0.0
        self.current_usage: float = 0.0
        self.current_temperature: Optional[float] = None
        
        # Tracking minimums (for statistics)
        self.minimum_average_frequency: Optional[float] = None
    
    def add_frequency(self, frequency: float) -> None:
        """Add a frequency measurement."""
        if frequency < 0:
            raise ValueError("Frequency cannot be negative")
        self.frequency_history.append(frequency)
        self.current_frequency = frequency
    
    def add_usage(self, usage: float) -> None:
        """Add a usage percentage measurement."""
        if not 0 <= usage <= 100:
            raise ValueError("Usage must be between 0 and 100 percent")
        self.usage_history.append(usage)
        self.current_usage = usage
    
    def add_temperature(self, temperature: Optional[float]) -> None:
        """Add a temperature measurement."""
        if temperature is not None and not 0 <= temperature <= 150:
            raise ValueError("Temperature must be between 0 and 150 degrees Celsius")
        self.temperature_history.append(temperature)
        self.current_temperature = temperature
    
    def get_average_frequency(self) -> float:
        """Calculate average frequency from history."""
        if not self.frequency_history:
            return 0.0
        return sum(self.frequency_history) / len(self.frequency_history)
    
    def get_average_usage(self) -> float:
        """Calculate average usage from history."""
        if not self.usage_history:
            return 0.0
        return sum(self.usage_history) / len(self.usage_history)
    
    def get_average_temperature(self) -> Optional[float]:
        """Calculate average temperature from history, ignoring None values."""
        if not self.temperature_history:
            return None
        
        valid_temps = [t for t in self.temperature_history if t is not None]
        if not valid_temps:
            return None
        
        return sum(valid_temps) / len(valid_temps)
    
    def update_minimum_average(self, max_frequency: float) -> None:
        """Update the minimum average frequency tracking."""
        if len(self.frequency_history) >= config.HISTORY_SECONDS:
            avg_freq = self.get_average_frequency()
            if self.minimum_average_frequency is None:
                self.minimum_average_frequency = avg_freq
            else:
                self.minimum_average_frequency = min(self.minimum_average_frequency, avg_freq)


class SystemMetrics:
    """Manages metrics for all CPU cores in the system."""
    
    def __init__(self, num_cores: int):
        self.num_cores = num_cores
        self.cores = [CoreMetrics(core_id=i) for i in range(num_cores)]
        self.max_frequency: float = 0.0
    
    def update_all_frequencies(self, frequencies: List[float], max_freq: float) -> None:
        """Update frequency data for all cores."""
        if len(frequencies) != self.num_cores:
            raise ValueError(f"Expected {self.num_cores} frequencies, got {len(frequencies)}")
        
        self.max_frequency = max_freq
        for core, freq in zip(self.cores, frequencies):
            core.add_frequency(freq)
    
    def update_all_usage(self, usage_percentages: List[float]) -> None:
        """Update usage data for all cores."""
        if len(usage_percentages) != self.num_cores:
            raise ValueError(f"Expected {self.num_cores} usage values, got {len(usage_percentages)}")
        
        for core, usage in zip(self.cores, usage_percentages):
            core.add_usage(usage)
    
    def update_all_temperatures(self, temperatures: List[Optional[float]]) -> None:
        """Update temperature data for all cores."""
        if len(temperatures) != self.num_cores:
            raise ValueError(f"Expected {self.num_cores} temperature values, got {len(temperatures)}")
        
        for core, temp in zip(self.cores, temperatures):
            core.add_temperature(temp)
    
    def get_current_frequencies(self) -> List[float]:
        """Get current frequency for all cores."""
        return [core.current_frequency for core in self.cores]
    
    def get_current_usage(self) -> List[float]:
        """Get current usage for all cores."""
        return [core.current_usage for core in self.cores]
    
    def get_current_temperatures(self) -> List[Optional[float]]:
        """Get current temperature for all cores."""
        return [core.current_temperature for core in self.cores]
    
    def get_average_frequencies(self) -> List[float]:
        """Get average frequencies for all cores."""
        return [core.get_average_frequency() for core in self.cores]
    
    def get_average_usage(self) -> List[float]:
        """Get average usage for all cores."""
        return [core.get_average_usage() for core in self.cores]
    
    def get_average_temperatures(self) -> List[Optional[float]]:
        """Get average temperatures for all cores."""
        return [core.get_average_temperature() for core in self.cores]
    
    def get_frequency_histories(self) -> List[Deque[float]]:
        """Get frequency histories for all cores (for backward compatibility)."""
        return [core.frequency_history for core in self.cores]
    
    def get_usage_histories(self) -> List[Deque[float]]:
        """Get usage histories for all cores (for backward compatibility)."""
        return [core.usage_history for core in self.cores]
    
    def get_temperature_histories(self) -> List[Deque[Optional[float]]]:
        """Get temperature histories for all cores (for backward compatibility)."""
        return [core.temperature_history for core in self.cores]
    
    def update_minimum_averages(self) -> None:
        """Update minimum average tracking for all cores."""
        for core in self.cores:
            core.update_minimum_average(self.max_frequency)
    
    def get_minimum_averages(self) -> List[Optional[float]]:
        """Get minimum average frequencies for all cores."""
        return [core.minimum_average_frequency for core in self.cores]


@dataclass
class AlertState:
    """Represents the current alert state of the system."""
    is_active: bool = False
    alert_type: str = "normal"
    critical_alert: bool = False
    message: str = ""
    
    def set_throttling_alert(self) -> None:
        """Set throttling alert state."""
        self.is_active = True
        self.alert_type = "throttling"
        self.critical_alert = True
        self.message = "⚠  THROTTLING: avg freq below 50% of max ⚠"
    
    def set_critical_temperature_alert(self, temp: float, core_id: int) -> None:
        """Set critical temperature alert state."""
        self.is_active = True
        self.alert_type = "critical_temperature"
        self.critical_alert = True
        self.message = f"🔥 CRITICAL: Core {core_id} temperature {temp:.1f}°C ≥ {config.TEMPERATURE_CRITICAL_THRESHOLD}°C"
    
    def clear_alerts(self) -> None:
        """Clear all alert states."""
        self.is_active = False
        self.alert_type = "normal"
        self.critical_alert = False
        self.message = ""


@dataclass
class DisplayArea:
    """Represents a rectangular area on the terminal screen."""
    x: int
    y: int
    width: int
    height: int
    
    def __post_init__(self):
        """Validate display area dimensions."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Display area dimensions must be positive")
    
    def as_tuple(self) -> tuple:
        """Return as a tuple for backward compatibility."""
        return (self.x, self.y, self.width, self.height)


@dataclass  
class GraphRenderParams:
    """Parameters for rendering graphs on the terminal."""
    screen: object  # curses screen object
    area: DisplayArea
    max_frequency: float
    is_alert_mode: bool
    stats_box_width: int
    
    def __post_init__(self):
        """Validate graph render parameters."""
        if self.max_frequency <= 0:
            raise ValueError("Maximum frequency must be positive")
        if self.stats_box_width < 0:
            raise ValueError("Stats box width cannot be negative")