import numpy as np


def volume(length, width, height):
    return float(length) * float(width) * float(height)


def utilization_percent(used_volume, lorry_volume):
    if lorry_volume <= 0:
        return 0.0
    return (float(used_volume) / float(lorry_volume)) * 100.0


def center_of_mass_xy(placements):
    if not placements:
        return 0.0, 0.0
    weights = np.asarray([float(p["loaded_weight"]) for p in placements], dtype=np.float64)
    total_weight = float(weights.sum())
    if total_weight <= 0:
        return 0.0, 0.0
    centers = np.asarray([
        (float(p["x"]) + float(p["placed_length"]) / 2,
         float(p["y"]) + float(p["placed_width"]) / 2)
        for p in placements
    ], dtype=np.float64)
    result = np.average(centers, axis=0, weights=weights)
    return float(result[0]), float(result[1])
