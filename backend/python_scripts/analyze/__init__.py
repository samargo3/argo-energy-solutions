"""
Analytics modules for energy data analysis (sensor health, after-hours waste, anomalies, spikes, quick wins)
"""

from .anomaly_detection import (
    detect_anomalies,
    analyze_anomalies,
    build_baseline_profile,
    generate_anomaly_timeline,
)

from .after_hours_waste import (
    calculate_after_hours_waste,
    analyze_after_hours_waste,
)

from .spike_detection import (
    detect_spikes,
    analyze_spikes,
    build_spike_baseline,
    get_top_spikes,
)

from .sensor_health import (
    analyze_sensor_health,
    analyze_sensor_health_for_site,
    generate_health_summary,
)

from .quick_wins import (
    generate_quick_wins,
)

__all__ = [
    # anomaly_detection
    'detect_anomalies',
    'analyze_anomalies',
    'build_baseline_profile',
    'generate_anomaly_timeline',
    # after_hours_waste
    'calculate_after_hours_waste',
    'analyze_after_hours_waste',
    # spike_detection
    'detect_spikes',
    'analyze_spikes',
    'build_spike_baseline',
    'get_top_spikes',
    # sensor_health
    'analyze_sensor_health',
    'analyze_sensor_health_for_site',
    'generate_health_summary',
    # quick_wins
    'generate_quick_wins',
]
