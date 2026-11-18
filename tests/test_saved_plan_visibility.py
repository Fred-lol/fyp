from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from psycopg.errors import DeadlockDetected

from services.optimization_service import get_plan, plan_is_current, saved_weight_utilization


def test_saved_plan_is_visible_through_its_thirtieth_day():
    now = datetime(2026, 11, 18, 8, tzinfo=timezone.utc)
    boundary = now - timedelta(days=30)
    assert plan_is_current(boundary, now)
    assert not plan_is_current(boundary - timedelta(microseconds=1), now)


def test_weight_percentage_uses_saved_capacity():
    assert saved_weight_utilization({"total_weight": 440, "remaining_weight_capacity": 560}) == 44
    assert saved_weight_utilization({"total_weight": 0, "remaining_weight_capacity": 0}) == 0


def test_plan_read_restarts_after_a_deadlock():
    plan = {"plan_id": 7}
    with patch("services.optimization_service._read_plan", side_effect=[DeadlockDetected(), plan]) as read:
        assert get_plan(7) == plan
        assert read.call_count == 2
