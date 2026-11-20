"""Deterministic multi-start 3D packing with an independently checked fallback.

This is a geometric heuristic, not machine learning.  The original first-fit
packing pass is retained as the fallback; the enhanced search compares legal
horizontal orientations and scored candidate placements under a fixed time
budget.  Every candidate is independently validated before it can succeed.
"""
from math import isfinite
from time import perf_counter

from optimization.constraints import orientations, fully_supported, loading_sequence_key, stack_loads_valid
from optimization.validation import boxes_overlap, inside_lorry, validate_plan
from optimization.scoring import volume, utilization_percent, center_of_mass_xy


BASELINE_STRATEGIES = (
    ("largest_first", "depth_first"),
    ("largest_first", "width_first"),
    ("heavy_first", "depth_first"),
    ("wide_first", "width_first"),
    ("wide_first", "balanced"),
)

ENHANCED_STRATEGIES = (
    ("largest_first", "section_first"),
    ("heavy_first", "section_first"),
    ("largest_first", "balanced"),
    ("heavy_first", "balanced"),
    ("footprint_first", "depth_first"),
    ("longest_first", "width_first"),
    ("heaviest_footprint", "contact_first"),
    ("wide_first", "balanced"),
    ("largest_first", "contact_first"),
    ("light_first", "depth_first"),
)


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
    if strategy == "balanced":
        return sorted(candidates, key=lambda point: (point[2], point[0] + point[1], point[1], point[0]))
    return sorted(candidates, key=lambda point: (point[2], point[1], point[0]))


def _ordered_boxes(boxes, strategy):
    if strategy == "heavy_first":
        key = lambda b: (float(b["loaded_weight"]), volume(b["length"], b["width"], b["height"]))
        reverse = True
    elif strategy == "wide_first":
        key = lambda b: (float(b["width"]), float(b["length"]), float(b["loaded_weight"]))
        reverse = True
    elif strategy == "footprint_first":
        key = lambda b: (float(b["length"]) * float(b["width"]), float(b["height"]))
        reverse = True
    elif strategy == "longest_first":
        key = lambda b: (max(float(b["length"]), float(b["width"])), min(float(b["length"]), float(b["width"])))
        reverse = True
    elif strategy == "heaviest_footprint":
        key = lambda b: (float(b["loaded_weight"]) / max(float(b["length"]) * float(b["width"]), 1e-9), volume(b["length"], b["width"], b["height"]))
        reverse = True
    elif strategy == "light_first":
        key = lambda b: (float(b["loaded_weight"]), volume(b["length"], b["width"], b["height"]))
        reverse = False
    else:
        key = lambda b: (volume(b["length"], b["width"], b["height"]), float(b["loaded_weight"]))
        reverse = True
    # Stable identifiers make repeated runs reproducible when sizes tie.
    return sorted(boxes, key=lambda b: (key(b), int(b["order_id"]), int(b["box_instance"])), reverse=reverse)


def _make_placement(box, position, dimensions):
    x, y, z = position
    length, width, height = dimensions
    order_id = int(box["order_id"])
    box_instance = int(box["box_instance"])
    return {
        "order_id": order_id,
        "box_profile_id": int(box["box_profile_id"]),
        "box_instance": box_instance,
        "box_label": box.get("box_label") or f"O{order_id}-B{box_instance:02d}",
        "customer_name": box.get("customer_name", "Customer"),
        "box_name": box.get("box_name", "Box"),
        "capacity_litre": int(box.get("capacity_litre") or 0),
        "x": float(x), "y": float(y), "z": float(z),
        "placed_length": float(length), "placed_width": float(width), "placed_height": float(height),
        "orientation": f"{length:g} x {width:g} x {height:g}",
        "sequence_number": 0,
        "loaded_weight": float(box["loaded_weight"]),
    }


def _pack_baseline_once(lorry, boxes, order_strategy, position_strategy):
    """Preserved original deterministic first-fit: canonical footprint only."""
    placements = []
    for box in _ordered_boxes(boxes, order_strategy):
        placed = None
        dimensions = (float(box["length"]), float(box["width"]), float(box["height"]))
        for position in _candidate_positions(placements, position_strategy):
            candidate = _make_placement(box, position, dimensions)
            if (inside_lorry(candidate, lorry)
                    and not any(boxes_overlap(candidate, existing) for existing in placements)
                    and fully_supported(candidate, placements)
                    and stack_loads_valid([*placements, candidate])):
                placed = candidate
                break
        if placed is None:
            return None
        placements.append(placed)
    return placements


def _contact_area(candidate, placements):
    """Approximate floor and face contact in square centimetres."""
    l, w, h = candidate["placed_length"], candidate["placed_width"], candidate["placed_height"]
    x, y, z = candidate["x"], candidate["y"], candidate["z"]
    contact = l * w if z <= 1e-9 else 0.0
    for other in placements:
        ox, oy, oz = other["x"], other["y"], other["z"]
        ol, ow, oh = other["placed_length"], other["placed_width"], other["placed_height"]
        overlap_x = max(0.0, min(x + l, ox + ol) - max(x, ox))
        overlap_y = max(0.0, min(y + w, oy + ow) - max(y, oy))
        overlap_z = max(0.0, min(z + h, oz + oh) - max(z, oz))
        if abs(z - (oz + oh)) <= 1e-9:
            contact += overlap_x * overlap_y
        if abs(x - (ox + ol)) <= 1e-9 or abs(x + l - ox) <= 1e-9:
            contact += overlap_y * overlap_z
        if abs(y - (oy + ow)) <= 1e-9 or abs(y + w - oy) <= 1e-9:
            contact += overlap_x * overlap_z
    return contact


def _placement_score(candidate, placements, lorry, strategy, moments):
    """Adaptive lexicographic score: floor-first, compact, balanced, supported."""
    x, y, z = candidate["x"], candidate["y"], candidate["z"]
    length, width, height = candidate["placed_length"], candidate["placed_width"], candidate["placed_height"]
    far_x = max(moments["far_x"], x + length)
    far_y = max(moments["far_y"], y + width)
    far_z = max(moments["far_z"], z + height)
    envelope = far_x * far_y * far_z
    weight = float(candidate["loaded_weight"])
    total = moments["weight"] + weight
    center_x = (moments["x_moment"] + (x + length / 2) * weight) / total
    center_y = (moments["y_moment"] + (y + width / 2) * weight) / total
    balance = abs(center_x - float(lorry["internal_length"]) / 2) + abs(center_y - float(lorry["internal_width"]) / 2)
    contact = _contact_area(candidate, placements)
    if strategy == "width_first":
        tie_breaker = (x, y)
    elif strategy == "balanced":
        tie_breaker = (abs(center_y - float(lorry["internal_width"]) / 2), x + y)
    else:
        tie_breaker = (y, x)
    if strategy == "section_first":
        return (round(far_x, 6), round(x, 6), round(z, 6), round(envelope, 6), -round(contact, 6), round(balance, 6))
    return (round(z, 6), round(envelope, 6), round(balance, 6), -round(contact, 6), *tie_breaker)


def _pack_enhanced_once(lorry, boxes, order_strategy, position_strategy, deadline):
    """Best-scored feasible placement for each box in one deterministic start."""
    placements = []
    for box in _ordered_boxes(boxes, order_strategy):
        if perf_counter() >= deadline:
            return None
        moments = {
            "weight": sum(float(p["loaded_weight"]) for p in placements),
            "x_moment": sum((p["x"] + p["placed_length"] / 2) * p["loaded_weight"] for p in placements),
            "y_moment": sum((p["y"] + p["placed_width"] / 2) * p["loaded_weight"] for p in placements),
            "far_x": max((p["x"] + p["placed_length"] for p in placements), default=0.0),
            "far_y": max((p["y"] + p["placed_width"] for p in placements), default=0.0),
            "far_z": max((p["z"] + p["placed_height"] for p in placements), default=0.0),
        }
        best = None
        best_score = None
        for position in _candidate_positions(placements, position_strategy):
            if perf_counter() >= deadline:
                return None
            for dimensions in orientations(box["length"], box["width"], box["height"]):
                candidate = _make_placement(box, position, dimensions)
                if (inside_lorry(candidate, lorry)
                        and not any(boxes_overlap(candidate, existing) for existing in placements)
                        and fully_supported(candidate, placements)
                    and stack_loads_valid([*placements, candidate])):
                    score = _placement_score(candidate, placements, lorry, position_strategy, moments)
                    if best_score is None or score < best_score:
                        best, best_score = candidate, score
        if best is None:
            return None
        placements.append(best)
    return placements


def _compactness_score(placements, lorry):
    far_x = max(item["x"] + item["placed_length"] for item in placements) - min(item["x"] for item in placements)
    far_y = max(item["y"] + item["placed_width"] for item in placements)
    far_z = max(item["z"] + item["placed_height"] for item in placements)
    center_x, center_y = center_of_mass_xy(placements)
    balance = abs(center_x - float(lorry["internal_length"]) / 2) + abs(center_y - float(lorry["internal_width"]) / 2)
    return (round(far_x * far_y * far_z, 6), round(far_z, 6), round(balance, 6), round(far_y, 6), round(far_x, 6))


def _finalise_deep_loading_sequence(placements, lorry):
    """Mirror the deep-origin packing into the truck and assign floor-to-top sequence."""
    lorry_length = float(lorry["internal_length"])
    for item in placements:
        item["x"] = lorry_length - item["x"] - item["placed_length"]
    placements.sort(key=loading_sequence_key)
    for sequence, item in enumerate(placements, start=1):
        item["sequence_number"] = sequence


def _input_errors(lorry, boxes):
    errors = []
    for field in ("internal_length", "internal_width", "internal_height", "max_weight"):
        try:
            value = float(lorry[field])
        except (KeyError, TypeError, ValueError):
            errors.append(f"Lorry {field.replace('_', ' ')} is missing or invalid.")
            continue
        if not isfinite(value) or value <= 0:
            errors.append(f"Lorry {field.replace('_', ' ')} must be a finite value greater than zero.")
    identities = set()
    for index, box in enumerate(boxes, start=1):
        for field in ("length", "width", "height", "loaded_weight"):
            try:
                value = float(box[field])
            except (KeyError, TypeError, ValueError):
                errors.append(f"Required box {index} has a missing or invalid {field.replace('_', ' ')}.")
                continue
            if not isfinite(value) or value <= 0:
                errors.append(f"Required box {index} {field.replace('_', ' ')} must be finite and greater than zero.")
        try:
            identity = (int(box["order_id"]), int(box["box_profile_id"]), int(box["box_instance"]))
        except (KeyError, TypeError, ValueError):
            errors.append(f"Required box {index} is missing its order, profile or instance identity.")
            continue
        if identity in identities:
            errors.append(f"Required box {index} repeats identity {identity}.")
        identities.add(identity)
    return errors


def _failure(message, *, placements=None):
    return {"success": False, "message": message, "placements": placements or []}


def generate_plan(lorry, boxes, *, time_limit_seconds=8.0):
    """Compare multi-start scored layouts with the preserved verified baseline."""
    started = perf_counter()
    boxes = list(boxes or [])
    if not boxes:
        return _failure("No boxes were provided for optimization.")
    errors = _input_errors(lorry, boxes)
    if errors:
        return _failure("Invalid loading input: " + " ".join(errors))
    total_weight = sum(float(box["loaded_weight"]) for box in boxes)
    maximum_weight = float(lorry["max_weight"])
    if total_weight > maximum_weight + 1e-9:
        return _failure(
            f"Loading capacity exceeded. Total load: {total_weight:,.0f} kg. "
            f"Lorry capacity: {maximum_weight:,.0f} kg. Please select a larger lorry or reduce the load."
        )

    lorry_volume = volume(lorry["internal_length"], lorry["internal_width"], lorry["internal_height"])
    required_volume = sum(volume(box["length"], box["width"], box["height"]) for box in boxes)
    if required_volume > lorry_volume + 1e-9:
        shortfall = required_volume - lorry_volume
        return _failure(
            f"{lorry.get('plate_number', 'Selected lorry')} cannot be used: the required insulated boxes need "
            f"{required_volume / 1_000_000:,.2f} m³, but the usable lorry space is only "
            f"{lorry_volume / 1_000_000:,.2f} m³ ({shortfall / 1_000_000:,.2f} m³ short). "
            "Choose a larger lorry or remove orders."
        )

    expected_weight_by_identity = {
        (int(b["order_id"]), int(b["box_profile_id"]), int(b["box_instance"])): float(b["loaded_weight"])
        for b in boxes
    }
    candidates = []
    baseline_placements = None
    baseline_score = None
    baseline_attempts = 0
    for order_strategy, position_strategy in BASELINE_STRATEGIES:
        baseline_attempts += 1
        candidate = _pack_baseline_once(lorry, boxes, order_strategy, position_strategy)
        if candidate:
            _finalise_deep_loading_sequence(candidate, lorry)
            valid, _ = validate_plan(candidate, lorry, total_weight, expected_boxes=boxes)
            if valid:
                baseline_placements = candidate
                baseline_score = _compactness_score(candidate, lorry)
                candidates.append((baseline_score, "baseline", order_strategy, position_strategy, candidate))
                break

    search_budget = min(max(float(time_limit_seconds), 0.0), 8.0)
    deadline = started + search_budget
    enhanced_count = 0
    enhanced_attempts = 0
    timed_out = False
    for order_strategy, position_strategy in ENHANCED_STRATEGIES:
        if perf_counter() >= deadline:
            timed_out = True
            break
        enhanced_attempts += 1
        candidate = _pack_enhanced_once(lorry, boxes, order_strategy, position_strategy, deadline)
        if candidate is None:
            timed_out = perf_counter() >= deadline
            if timed_out:
                break
            continue
        _finalise_deep_loading_sequence(candidate, lorry)
        valid, _ = validate_plan(candidate, lorry, total_weight, expected_boxes=boxes)
        if valid:
            enhanced_count += 1
            candidates.append((_compactness_score(candidate, lorry), "enhanced", order_strategy, position_strategy, candidate))

    if not candidates:
        if timed_out:
            reason = "The enhanced search reached its time limit and no complete baseline layout passed validation."
        else:
            reason = "The selected boxes cannot be arranged safely inside this lorry. Their dimensions or safe stacking requirements do not form a valid complete 3D layout. Choose a larger lorry or split the orders."
        return _failure(reason)

    score, method, order_strategy, position_strategy, placements = min(candidates, key=lambda item: item[0])
    valid, errors = validate_plan(placements, lorry, total_weight, expected_boxes=boxes)
    if not valid:
        return _failure("Independent loading-plan validation failed: " + " ".join(errors), placements=placements)

    used_volume = sum(volume(item["placed_length"], item["placed_width"], item["placed_height"]) for item in placements)
    utilization = utilization_percent(used_volume, lorry_volume)
    weight_utilization = utilization_percent(total_weight, float(lorry["max_weight"]))
    center_x, center_y = center_of_mass_xy(placements)
    elapsed = perf_counter() - started
    if method == "baseline" and timed_out:
        message = "Enhanced search reached its time limit; the original baseline layout passed independent validation and was selected."
    else:
        message = "Best complete loading arrangement selected from validated baseline and multi-start horizontal search."
    return {
        "success": True,
        "message": message,
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
            "optimizer_strategy": f"{method} / {order_strategy.replace('_', '-')} / {position_strategy.replace('_', '-')}",
            "search_method": "deterministic multi-start geometric heuristic; no machine learning",
            "baseline_candidate_valid": baseline_placements is not None,
            "baseline_score": baseline_score,
            "selected_score": score,
            "enhanced_candidates_validated": enhanced_count,
            "baseline_strategies_evaluated": baseline_attempts,
            "enhanced_strategies_evaluated": enhanced_attempts,
            "search_timed_out": timed_out,
            "optimization_seconds": elapsed,
            "numpy_metrics_used": True,
        },
    }
