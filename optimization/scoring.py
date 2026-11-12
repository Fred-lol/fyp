def volume(length, width, height):
    return float(length) * float(width) * float(height)


def utilization_percent(used_volume, lorry_volume):
    if lorry_volume <= 0:
        return 0.0
    return (float(used_volume) / float(lorry_volume)) * 100.0


def center_of_mass_xy(placements):
    total_weight = sum(float(p["loaded_weight"]) for p in placements)
    if total_weight <= 0:
        return 0.0, 0.0
    x = sum((p["x"] + p["placed_length"] / 2) * p["loaded_weight"] for p in placements) / total_weight
    y = sum((p["y"] + p["placed_width"] / 2) * p["loaded_weight"] for p in placements) / total_weight
    return x, y
