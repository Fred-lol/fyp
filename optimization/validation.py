from optimization.constraints import fully_supported


def boxes_overlap(a, b, eps=1e-9):
    return not (
        a["x"] + a["placed_length"] <= b["x"] + eps
        or b["x"] + b["placed_length"] <= a["x"] + eps
        or a["y"] + a["placed_width"] <= b["y"] + eps
        or b["y"] + b["placed_width"] <= a["y"] + eps
        or a["z"] + a["placed_height"] <= b["z"] + eps
        or b["z"] + b["placed_height"] <= a["z"] + eps
    )


def inside_lorry(p, lorry, eps=1e-9):
    return (
        p["x"] >= -eps
        and p["y"] >= -eps
        and p["z"] >= -eps
        and p["x"] + p["placed_length"] <= lorry["internal_length"] + eps
        and p["y"] + p["placed_width"] <= lorry["internal_width"] + eps
        and p["z"] + p["placed_height"] <= lorry["internal_height"] + eps
    )


def validate_plan(placements, lorry, total_weight):
    errors = []
    if total_weight > float(lorry["max_weight"]) + 1e-9:
        errors.append("Total loaded weight exceeds lorry maximum weight.")
    for i, p in enumerate(placements):
        if not inside_lorry(p, lorry):
            errors.append(f"Placement {i + 1} is outside the lorry boundary.")
        if not fully_supported(p, placements[:i]):
            errors.append(f"Placement {i + 1} is not safely supported by the lorry floor or a suitable box.")
        for j in range(i):
            if boxes_overlap(p, placements[j]):
                errors.append(f"Placements {j + 1} and {i + 1} overlap.")
    return len(errors) == 0, errors
