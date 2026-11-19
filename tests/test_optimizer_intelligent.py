from copy import deepcopy
from time import perf_counter

import pytest

from optimization.constraints import orientations
from optimization.optimizer import generate_plan
from optimization.validation import validate_plan


def lorry(length=200, width=100, height=100, weight=1000):
    return {"plate_number": "TEST", "internal_length": float(length), "internal_width": float(width),
            "internal_height": float(height), "max_weight": float(weight)}


def box(instance=1, length=50, width=40, height=30, weight=20, profile=1):
    return {"order_id": 10, "box_profile_id": profile, "box_instance": instance,
            "box_name": f"{profile}L Test Box", "capacity_litre": profile,
            "length": float(length), "width": float(width), "height": float(height),
            "loaded_weight": float(weight)}


def test_horizontal_rotation_is_compared_but_upright_rotation_is_forbidden():
    assert orientations(70, 50, 30) == [(70.0, 50.0, 30.0), (50.0, 70.0, 30.0)]
    assert orientations(50, 50, 30) == [(50.0, 50.0, 30.0)]


def test_multi_start_horizontal_search_solves_case_canonical_baseline_cannot():
    truck = lorry(length=50, width=70, height=35)
    required = [box(length=70, width=50, height=30)]
    result = generate_plan(truck, required)
    assert result["success"], result["message"]
    assert result["placements"][0]["placed_length"] == 50
    assert result["placements"][0]["placed_width"] == 70
    assert result["placements"][0]["placed_height"] == 30
    assert result["metrics"]["baseline_candidate_valid"] is False
    assert "multi-start geometric heuristic" in result["metrics"]["search_method"]
    assert "no machine learning" in result["metrics"]["search_method"]
    assert validate_plan(result["placements"], truck, 20, expected_boxes=required)[0]


def test_search_is_reproducible_and_never_scores_worse_than_valid_baseline():
    truck = lorry(200, 100, 100)
    required = [box(i, length=(35 if i % 2 else 50), width=30, height=25, weight=12 + i) for i in range(1, 9)]
    first = generate_plan(truck, required)
    second = generate_plan(truck, required)
    assert first["success"] and second["success"]
    fields = ("box_instance", "x", "y", "z", "placed_length", "placed_width", "placed_height", "sequence_number")
    assert [[p[k] for k in fields] for p in first["placements"]] == [[p[k] for k in fields] for p in second["placements"]]
    metrics = first["metrics"]
    if metrics["baseline_candidate_valid"]:
        assert metrics["selected_score"] <= metrics["baseline_score"]


def test_all_required_boxes_and_accurate_volume_weight_metrics():
    truck = lorry(200, 100, 100, 500)
    required = [box(1), box(2), box(3, profile=2)]
    result = generate_plan(truck, required)
    assert result["success"], result["message"]
    metrics = result["metrics"]
    assert metrics["total_boxes"] == len(required)
    assert len({(p["order_id"], p["box_profile_id"], p["box_instance"]) for p in result["placements"]}) == 3
    assert metrics["total_weight"] == pytest.approx(60)
    assert metrics["used_volume"] == pytest.approx(sum(p["placed_length"] * p["placed_width"] * p["placed_height"] for p in result["placements"]))
    assert metrics["remaining_volume"] == pytest.approx(metrics["lorry_volume"] - metrics["used_volume"])
    assert metrics["space_utilization"] == pytest.approx(100 * metrics["used_volume"] / metrics["lorry_volume"])
    assert metrics["weight_utilization"] == pytest.approx(12)


@pytest.mark.parametrize("mutate", [
    lambda placements: placements.pop(),
    lambda placements: placements.append(deepcopy(placements[0])),
    lambda placements: placements[0].update(x=-1),
    lambda placements: placements[0].update(loaded_weight=19),
    lambda placements: placements[0].update(placed_height=999),
    lambda placements: placements[0].update(sequence_number=99),
])
def test_independent_validator_rejects_incomplete_duplicate_or_corrupt_plans(mutate):
    truck = lorry()
    required = [box(1), box(2)]
    result = generate_plan(truck, required)
    assert result["success"], result["message"]
    placements = deepcopy(result["placements"])
    mutate(placements)
    valid, errors = validate_plan(placements, truck, 40, expected_boxes=required)
    assert not valid
    assert errors


def test_independent_validator_rejects_overlap_bad_support_and_wrong_total():
    truck = lorry(100, 80, 80, 500)
    required = [box(1), box(2)]
    result = generate_plan(truck, required)
    assert result["success"]
    overlap = deepcopy(result["placements"])
    overlap[1]["x"], overlap[1]["y"], overlap[1]["z"] = overlap[0]["x"], overlap[0]["y"], overlap[0]["z"]
    assert not validate_plan(overlap, truck, 40, expected_boxes=required)[0]
    assert not validate_plan(result["placements"], truck, 39, expected_boxes=required)[0]

    unstable = [
        {**box(1, weight=10), "x": 0.0, "y": 0.0, "z": 0.0,
         "placed_length": 50.0, "placed_width": 40.0, "placed_height": 30.0,
         "orientation": "50 x 40 x 30", "sequence_number": 1},
        {**box(2, weight=20), "x": 0.0, "y": 0.0, "z": 30.0,
         "placed_length": 50.0, "placed_width": 40.0, "placed_height": 30.0,
         "orientation": "50 x 40 x 30", "sequence_number": 2},
    ]
    assert not validate_plan(unstable, truck, 30, expected_boxes=[box(1, weight=10), box(2, weight=20)])[0]


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_invalid_lorry_and_box_dimensions_fail_closed(bad):
    invalid_truck = lorry()
    invalid_truck["internal_width"] = bad
    assert not generate_plan(invalid_truck, [box()])["success"]
    invalid_box = box()
    invalid_box["height"] = bad
    assert not generate_plan(lorry(), [invalid_box])["success"]


def test_capacity_and_impossible_mixed_dimensions_fail_with_specific_reason():
    too_heavy = generate_plan(lorry(weight=10), [box(weight=20)])
    assert not too_heavy["success"]
    assert "over capacity" in too_heavy["message"]

    impossible = generate_plan(lorry(100, 100, 30), [box(1, 60, 60, 30), box(2, 60, 60, 30)])
    assert not impossible["success"]
    assert "cannot be arranged safely" in impossible["message"]


def test_expected_workload_finishes_within_ten_seconds():
    truck = lorry(600, 250, 200, 10_000)
    required = [box(i, length=40, width=30, height=20, weight=15, profile=50) for i in range(1, 51)]
    started = perf_counter()
    result = generate_plan(truck, required)
    elapsed = perf_counter() - started
    assert result["success"], result["message"]
    assert elapsed < 10.0
    assert len(result["placements"]) == 50

