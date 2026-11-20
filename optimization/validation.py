"""Independent, fail-closed validation for packing coordinates and sequences."""
from math import isfinite

from optimization.constraints import fully_supported, loading_sequence_key, stack_loads_valid

EPS = 1e-7


def boxes_overlap(a, b, eps=EPS):
    return not (
        a["x"] + a["placed_length"] <= b["x"] + eps
        or b["x"] + b["placed_length"] <= a["x"] + eps
        or a["y"] + a["placed_width"] <= b["y"] + eps
        or b["y"] + b["placed_width"] <= a["y"] + eps
        or a["z"] + a["placed_height"] <= b["z"] + eps
        or b["z"] + b["placed_height"] <= a["z"] + eps
    )


def inside_lorry(p, lorry, eps=EPS):
    try:
        return (
            p["x"] >= -eps
            and p["y"] >= -eps
            and p["z"] >= -eps
            and p["x"] + p["placed_length"] <= float(lorry["internal_length"]) + eps
            and p["y"] + p["placed_width"] <= float(lorry["internal_width"]) + eps
            and p["z"] + p["placed_height"] <= float(lorry["internal_height"]) + eps
        )
    except (KeyError, TypeError, ValueError):
        return False


def _identity(row):
    return int(row["order_id"]), int(row["box_profile_id"]), int(row["box_instance"])


def _finite_positive(value):
    try:
        return isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def validate_plan(placements, lorry, total_weight, expected_boxes=None):
    """Validate all physical and accounting invariants before plan success/save.

    ``expected_boxes`` is the optimizer input and lets validation independently
    detect missing, duplicated, overweight, or incorrectly rotated boxes.
    """
    errors = []
    placements = list(placements or [])
    expected_boxes = list(expected_boxes) if expected_boxes is not None else None
    if not placements:
        errors.append("A loading plan must contain at least one box.")
    for field in ("internal_length", "internal_width", "internal_height", "max_weight"):
        if not _finite_positive(lorry.get(field) if hasattr(lorry, "get") else None):
            errors.append(f"Lorry {field.replace('_', ' ')} must be finite and greater than zero.")
    try:
        allowed_weight = float(lorry["max_weight"])
        claimed_weight = float(total_weight)
    except (KeyError, TypeError, ValueError):
        allowed_weight, claimed_weight = 0.0, float("nan")
    if not isfinite(claimed_weight) or claimed_weight < 0:
        errors.append("Total loaded weight must be finite and non-negative.")
    elif claimed_weight > allowed_weight + EPS:
        errors.append("Total loaded weight exceeds lorry maximum weight.")

    required = {}
    if expected_boxes is not None:
        for box in expected_boxes:
            try:
                required[_identity(box)] = box
            except (KeyError, TypeError, ValueError):
                errors.append("Expected box data is missing a valid identity.")

    seen = set()
    sequence_numbers = []
    computed_weight = 0.0
    valid_prior = []
    for i, p in enumerate(placements):
        try:
            identity = _identity(p)
        except (KeyError, TypeError, ValueError):
            errors.append(f"Placement {i + 1} is missing its order, profile or instance identity.")
            identity = None
        if identity is not None:
            if identity in seen:
                errors.append(f"Placement {i + 1} duplicates box identity {identity}.")
            seen.add(identity)

        fields = ("x", "y", "z", "placed_length", "placed_width", "placed_height", "loaded_weight")
        values = {}
        for field in fields:
            try:
                values[field] = float(p[field])
            except (KeyError, TypeError, ValueError):
                errors.append(f"Placement {i + 1} has a missing or invalid {field.replace('_', ' ')}.")
                values[field] = float("nan")
        if not all(isfinite(value) for value in values.values()):
            errors.append(f"Placement {i + 1} contains a non-finite dimension, coordinate or weight.")
            continue
        if any(values[name] <= 0 for name in ("placed_length", "placed_width", "placed_height", "loaded_weight")):
            errors.append(f"Placement {i + 1} dimensions and loaded weight must be greater than zero.")
        computed_weight += values["loaded_weight"]
        try:
            sequence = int(p["sequence_number"])
            if sequence != p["sequence_number"]:
                raise ValueError
            sequence_numbers.append(sequence)
        except (KeyError, TypeError, ValueError):
            errors.append(f"Placement {i + 1} has an invalid loading sequence number.")

        if not inside_lorry(p, lorry):
            errors.append(f"Placement {i + 1} is outside the lorry's internal boundaries.")
        if not fully_supported(p, valid_prior):
            errors.append(f"Placement {i + 1} is not safely supported by the floor or an earlier box.")
        for j, prior in enumerate(valid_prior):
            if boxes_overlap(p, prior):
                errors.append(f"A prior placement and placement {i + 1} overlap.")

        if identity is not None and expected_boxes is not None and identity in required:
            box = required[identity]
            try:
                legal = (
                    (float(box["length"]), float(box["width"]), float(box["height"])),
                    (float(box["width"]), float(box["length"]), float(box["height"])),
                )
                placed_dims = (values["placed_length"], values["placed_width"], values["placed_height"])
                if not any(all(abs(a - b) <= EPS for a, b in zip(placed_dims, option)) for option in legal):
                    errors.append(f"Placement {i + 1} uses an unsupported orientation or incorrect box dimensions.")
                if abs(values["loaded_weight"] - float(box["loaded_weight"])) > EPS:
                    errors.append(f"Placement {i + 1} loaded weight does not match the required box weight.")
                expected_orientation = f"{values['placed_length']:g} x {values['placed_width']:g} x {values['placed_height']:g}"
                if p.get("orientation") != expected_orientation:
                    errors.append(f"Placement {i + 1} orientation label does not match its placed dimensions.")
            except (KeyError, TypeError, ValueError):
                errors.append(f"Placement {i + 1} cannot be matched to valid expected box data.")
        if all(values[name] > 0 for name in ("placed_length", "placed_width", "placed_height", "loaded_weight")):
            valid_prior.append(p)

    if len(valid_prior) == len(placements) and not stack_loads_valid(valid_prior):
        errors.append("Cumulative stack load exceeds the supporting box limit.")

    if sequence_numbers and sequence_numbers != list(range(1, len(placements) + 1)):
        errors.append("Loading sequence numbers must be unique and consecutive from 1.")
    try:
        physical_order = sorted(
            placements,
            key=loading_sequence_key,
        )
        if [p.get("sequence_number") for p in physical_order] != [p.get("sequence_number") for p in placements]:
            errors.append("Loading sequence must proceed from the deepest end toward the rear gate, with supporting boxes first.")
    except (KeyError, TypeError, ValueError):
        errors.append("Loading sequence cannot be validated because placement coordinates or identities are invalid.")

    if abs(computed_weight - claimed_weight) > max(EPS, abs(claimed_weight) * 1e-9):
        errors.append("Total weight does not match the sum of the box weights.")

    if expected_boxes is not None:
        expected_ids = set(required)
        if seen != expected_ids:
            missing = expected_ids - seen
            unexpected = seen - expected_ids
            if missing:
                errors.append(f"Loading plan is incomplete: {len(missing)} required box(es) are missing.")
            if unexpected:
                errors.append(f"Loading plan contains {len(unexpected)} unexpected box(es).")
        expected_weight = sum(float(box["loaded_weight"]) for box in expected_boxes)
        if abs(expected_weight - claimed_weight) > max(EPS, abs(expected_weight) * 1e-9):
            errors.append("Claimed total weight does not match all required boxes.")

    # The center of mass must be within the lorry's supported floor area.
    center_rows = []
    for p in placements:
        try:
            row = tuple(float(p[key]) for key in ("x", "y", "placed_length", "placed_width", "loaded_weight"))
            if all(isfinite(value) for value in row):
                center_rows.append(row)
        except (KeyError, TypeError, ValueError):
            continue
    center_weight = sum(row[4] for row in center_rows)
    if center_weight > 0 and all(_finite_positive(lorry.get(f"internal_{axis}")) for axis in ("length", "width")):
        center_x = sum((x + length / 2) * weight for x, y, length, width, weight in center_rows) / center_weight
        center_y = sum((y + width / 2) * weight for x, y, length, width, weight in center_rows) / center_weight
        if not (-EPS <= center_x <= float(lorry["internal_length"]) + EPS
                and -EPS <= center_y <= float(lorry["internal_width"]) + EPS):
            errors.append("Load center of mass falls outside the lorry's floor support area.")
    return not errors, errors
