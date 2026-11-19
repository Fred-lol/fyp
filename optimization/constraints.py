def orientations(length, width, height):
    """Return legal horizontal footprints; box height is never rotated upright."""
    length, width, height = float(length), float(width), float(height)
    result = [(length, width, height)]
    if abs(length - width) > 1e-9:
        result.append((width, length, height))
    return result


def fully_supported(candidate, placements, eps=1e-9):
    """Conservative stacking rule: a raised box must sit entirely on one box.
    This avoids floating boxes and keeps the prototype loading guide stable.
    """
    if candidate["z"] <= eps:
        return True
    for base in placements:
        top = base["z"] + base["placed_height"]
        if abs(top - candidate["z"]) > eps:
            continue
        covers_x = base["x"] <= candidate["x"] + eps and base["x"] + base["placed_length"] >= candidate["x"] + candidate["placed_length"] - eps
        covers_y = base["y"] <= candidate["y"] + eps and base["y"] + base["placed_width"] >= candidate["y"] + candidate["placed_width"] - eps
        if covers_x and covers_y:
            # Heavy-on-light prevention: supported box must not be lighter.
            return float(candidate["loaded_weight"]) <= float(base["loaded_weight"]) + eps
    return False
