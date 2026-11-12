def orientations(length, width, height):
    """Return only safe horizontal orientations for insulated fish boxes.

    The physical length, width, and height are fixed for the loading guide.
    This prevents both upright placement and 90-degree turning, so matching
    insulated-box templates always render at exactly the same size.
    """
    length, width, height = float(length), float(width), float(height)
    return [(length, width, height)]


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
