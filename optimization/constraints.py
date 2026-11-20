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


def loading_sequence_key(p):
    """Deepest face first; equal-depth supports precede their upper boxes."""
    return (-(float(p["x"]) + float(p["placed_length"])), float(p["z"]),
            float(p["y"]), -float(p["x"]), int(p.get("order_id", 0)),
            int(p.get("box_instance", 0)))


def stack_loads_valid(placements, eps=1e-7):
    """Propagate all upper loads; unknown ratings use conservative loaded mass."""
    from math import isfinite
    loads = {id(p): 0.0 for p in placements}
    for p in sorted(placements, key=lambda p: float(p["z"]), reverse=True):
        limit = float(p.get("max_stack_load_kg", p["loaded_weight"]))
        if not isfinite(limit) or limit < 0 or loads[id(p)] > limit + eps:
            return False
        if float(p["z"]) <= eps:
            continue
        bases = [b for b in placements if b is not p and fully_supported(p, [b])]
        if not bases:
            return False
        base = bases[0]
        loads[id(base)] += float(p["loaded_weight"]) + loads[id(p)]
    return True
