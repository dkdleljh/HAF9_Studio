"""Metric calculators for spatial simulation zones."""

from __future__ import annotations

from math import fsum

from ..domain.spatial import Exit, Zone


def calculate_evacuation_time(zone: Zone, exits: list[Exit]) -> float:
    """Estimates zone evacuation time in seconds."""
    if not zone.cells or not exits:
        return 0.0

    x_mean = fsum(x for x, _ in zone.cells) / len(zone.cells)
    y_mean = fsum(y for _, y in zone.cells) / len(zone.cells)

    min_distance = min(
        abs(x_mean - exit_obj.location[0]) + abs(y_mean - exit_obj.location[1])
        for exit_obj in exits
    )
    total_capacity = fsum(
        exit_obj.capacity * (1.2 if exit_obj.is_emergency else 1.0)
        for exit_obj in exits
    )
    density_factor = 1.0 + calculate_crowd_density(zone)

    throughput_penalty = len(zone.cells) / max(total_capacity, 1.0)
    time_seconds = (min_distance * 0.85 + throughput_penalty * 5.0) * density_factor
    return round(time_seconds, 3)


def calculate_crowd_density(zone: Zone) -> float:
    """Calculates normalized crowd density in [0, 1]."""
    if not zone.cells:
        return 0.0

    nominal_capacity = 64.0
    density = len(zone.cells) / nominal_capacity
    return round(min(max(density, 0.0), 1.0), 4)


def calculate_peak_stress(zone: Zone) -> float:
    """Computes synthetic peak stress index for the zone."""
    density = calculate_crowd_density(zone)
    accessibility = calculate_accessibility(zone)
    noise = calculate_noise_level(zone)

    stress = density * 0.6 + (1.0 - accessibility) * 0.25 + (noise / 100.0) * 0.15
    return round(min(max(stress, 0.0), 1.0), 4)


def calculate_accessibility(zone: Zone) -> float:
    """Estimates accessibility score in [0, 1]."""
    if not zone.cells:
        return 1.0

    spread = len(zone.cells)
    score = 1.0 - min(spread / 180.0, 0.65)
    return round(min(max(score, 0.0), 1.0), 4)


def calculate_noise_level(zone: Zone) -> float:
    """Estimates average zone noise in dB."""
    if zone.noise_level > 0:
        return round(zone.noise_level, 3)

    base_noise = 35.0
    variable_noise = calculate_crowd_density(zone) * 45.0
    return round(base_noise + variable_noise, 3)
