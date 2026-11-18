"""Smart, deterministic 3D packing for AquaLoad loading plans.

It evaluates several packing strategies, validates each physical layout, then
selects the most compact safe plan.  This keeps recommendations repeatable
and auditable for warehouse staff.
"""

from optimization.constraints import orientations, fully_supported
from optimization.validation import boxes_overlap, inside_lorry, validate_plan
from optimization.scoring import volume, utilization_percent, center_of_mass_xy

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except Exception:
    ORTOOLS_AVAILABLE = False


def _orientation_score(dimensions, x, y, z):
    length, width, height = dimensions
    return (z + height) * 1_000_000 + (y + width) * 1_000 + (x + length)


def _choose_orientation(feasible, x, y, z):
    if not feasible:
        return None
    if not ORTOOLS_AVAILABLE or len(feasible) == 1:
        return min(feasible, key=lambda dim: _orientation_score(dim, x, y, z))
    model = cp_model.CpModel()
    choices = [model.NewBoolVar(f"orientation_{index}") for index in range(len(feasible))]
    model.Add(sum(choices) == 1)
    scores = [int(_orientation_score(dim, x, y, z) * 1000) for dim in feasible]
    model.Minimize(sum(choice * score for choice, score in zip(choices, scores)))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 0.05
    if solver.Solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return next(dim for choice, dim in zip(choices, feasible) if solver.Value(choice))
    return min(feasible, key=lambda dim: _orientation_score(dim, x, y, z))


def _candidate_positions(placements, strategy):
    candidates = {(0.0, 0.0, 0.0)}
    for item in placements:
        candidates.add((item["x"] + item["placed_length"], item["y"], item["z"]))
        candidates.add((item["x"], item["y"] + item["placed_width"], item["z"]))
        candidates.add((item["x"], item["y"], item["z"] + item["placed_height"]))
    if strategy == "depth_first":
        return sorted(candidates, key=lambda point: (point[2], point[1], point[0]))
    if strategy == "width_first":
        return sorted(candidates, key=lambda point: (point[2], point[0], point[1]))
    return sorted(candidates, key=lambda point: (point[2], point[0] + point[1], point[1], point[0]))


def _ordered_boxes(boxes, strategy):
    if strategy == "heavy_first":
        key = lambda box: (float(box["loaded_weight"]), volume(box["length"], box["width"], box["height"]))
    elif strategy == "wide_first":
        key = lambda box: (float(box["width"]), float(box["length"]), float(box["loaded_weight"]))
    else:
        key = lambda box: (volume(box["length"], box["width"], box["height"]), float(box["loaded_weight"]))
    return sorted(boxes, key=key, reverse=True)


def _pack_once(lorry, boxes, order_strategy, position_strategy):
    """Try one candidate-position strategy without changing database state."""
    placements = []
    for box in _ordered_boxes(boxes, order_strategy):
        placed = None
        for x, y, z in _candidate_positions(placements, position_strategy):
            feasible = []
            for dimensions in orientations(box["length"], box["width"], box["height"]):
                length, width, height = dimensions
                candidate = {
                    "x": x, "y": y, "z": z,
                    "placed_length": length, "placed_width": width, "placed_height": height,
                    "loaded_weight": float(box["loaded_weight"]),
                }
                if (inside_lorry(candidate, lorry)
                        and not any(boxes_overlap(candidate, existing) for existing in placements)
                        and fully_supported(candidate, placements)):
                    feasible.append(dimensions)
            dimensions = _choose_orientation(feasible, x, y, z)
            if dimensions:
                length, width, height = dimensions
                placed = {
                    "order_id": int(box["order_id"]),
                    "box_profile_id": int(box["box_profile_id"]),
                    "box_instance": int(box["box_instance"]),
                    "box_label": box.get("box_label") or f"O{int(box['order_id'])}-B{int(box['box_instance']):02d}",
                    "customer_name": box.get("customer_name", "Customer"),
                    "box_name": box.get("box_name", "Box"),
                    "capacity_litre": int(box.get("capacity_litre") or 0),
                    "x": float(x), "y": float(y), "z": float(z),
                    "placed_length": float(length), "placed_width": float(width), "placed_height": float(height),
                    "orientation": f"{length:g} x {width:g} x {height:g}",
                    "sequence_number": 0,
                    "loaded_weight": float(box["loaded_weight"]),
                }
                break
        if not placed:
            return None
        placements.append(placed)
    return placements


def _compactness_score(placements, lorry):
    """Lower is better: a smaller envelope, lower stack and balanced load."""
    far_x = max(item["x"] + item["placed_length"] for item in placements)
    far_y = max(item["y"] + item["placed_width"] for item in placements)
    far_z = max(item["z"] + item["placed_height"] for item in placements)
    envelope = far_x * far_y * far_z
    total_weight = sum(item["loaded_weight"] for item in placements) or 1
    weighted_y = sum((item["y"] + item["placed_width"] / 2) * item["loaded_weight"] for item in placements)
    lateral_offset = abs(weighted_y / total_weight - float(lorry["internal_width"]) / 2)
    return (round(envelope, 6), round(far_z, 6), round(lateral_offset, 6), round(far_y, 6))


def _finalise_deep_loading_sequence(placements, lorry):
    """Put compact packing at the deep end and create a practical sequence."""
    lorry_length = float(lorry["internal_length"])
    for item in placements:
        item["x"] = lorry_length - item["x"] - item["placed_length"]
    placements.sort(key=lambda item: (item["z"], -item["x"], item["y"], item["order_id"], item["box_instance"]))
    for sequence, item in enumerate(placements, start=1):
        item["sequence_number"] = sequence


def generate_plan(lorry, boxes):
    """Return the best valid arrangement found across multiple strategies."""
    if not boxes:
        return {"success": False, "message": "No boxes were provided for optimization."}
    total_weight = sum(float(box["loaded_weight"]) for box in boxes)
    maximum_weight = float(lorry["max_weight"] or 0)
    if total_weight > maximum_weight + 1e-9:
        return {
            "success": False,
            "message": (
                f"{lorry.get('plate_number', 'Selected lorry')} cannot be used: selected orders total "
                f"{total_weight:,.0f} kg, but its maximum is {maximum_weight:,.0f} kg "
                f"({total_weight - maximum_weight:,.0f} kg over capacity)."
            ),
        }

    lorry_volume = volume(lorry["internal_length"], lorry["internal_width"], lorry["internal_height"])
    required_volume = sum(volume(box["length"], box["width"], box["height"]) for box in boxes)
    if required_volume > lorry_volume + 1e-9:
        shortfall = required_volume - lorry_volume
        return {
            "success": False,
            "message": (
                f"{lorry.get('plate_number', 'Selected lorry')} cannot be used: the required insulated boxes need "
                f"{required_volume / 1_000_000:,.2f} m³, but the usable lorry space is only "
                f"{lorry_volume / 1_000_000:,.2f} m³ ({shortfall / 1_000_000:,.2f} m³ short). "
                "Choose a larger lorry or remove orders."
            ),
            "placements": [],
        }

    strategies = (
        ("largest_first", "depth_first"),
        ("largest_first", "width_first"),
        ("heavy_first", "depth_first"),
        ("wide_first", "width_first"),
        ("wide_first", "balanced"),
    )
    candidates = []
    for order_strategy, position_strategy in strategies:
        placements = _pack_once(lorry, boxes, order_strategy, position_strategy)
        if placements:
            candidates.append((_compactness_score(placements, lorry), order_strategy, position_strategy, placements))
    if not candidates:
        return {
            "success": False,
            "message": (
                "The selected boxes cannot be arranged safely inside this lorry. "
                "Their dimensions or safe stacking requirements do not form a valid 3D layout, even though the "
                "total box volume fits. Choose a lorry with larger internal dimensions or split the orders."
            ),
            "placements": [],
        }

    _, order_strategy, position_strategy, placements = min(candidates, key=lambda item: item[0])
    _finalise_deep_loading_sequence(placements, lorry)
    valid, errors = validate_plan(placements, lorry, total_weight)
    if not valid:
        return {"success": False, "message": "; ".join(errors), "placements": placements}

    used_volume = sum(volume(item["placed_length"], item["placed_width"], item["placed_height"]) for item in placements)
    utilization = utilization_percent(used_volume, lorry_volume)
    weight_utilization = utilization_percent(total_weight, float(lorry["max_weight"]))
    center_x, center_y = center_of_mass_xy(placements)
    return {
        "success": True,
        "message": "Smart optimizer selected the most compact valid loading arrangement.",
        "placements": placements,
        "metrics": {
            "total_boxes": len(placements),
            "lorry_volume": lorry_volume,
            "used_volume": used_volume,
            "remaining_volume": max(lorry_volume - used_volume, 0.0),
            "space_utilization": utilization,
            "weight_utilization": weight_utilization,
            "total_weight": total_weight,
            "remaining_weight_capacity": max(float(lorry["max_weight"]) - total_weight, 0.0),
            "center_of_mass_x": center_x,
            "center_of_mass_y": center_y,
            "optimizer_strategy": f"{order_strategy.replace('_', '-')} / {position_strategy.replace('_', '-')}",
            "strategies_evaluated": len(strategies),
            "ortools_used": ORTOOLS_AVAILABLE,
        },
    }
