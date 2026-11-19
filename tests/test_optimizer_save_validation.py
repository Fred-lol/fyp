from contextlib import contextmanager

from optimization.optimizer import generate_plan
from services import optimization_service


class QueryResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = list(rows or [])
        self.rowcount = 0
        self.lastrowid = 0

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class SaveConnection:
    def __init__(self, lorry, required_rows):
        self.lorry = lorry
        self.required_rows = required_rows
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if "FROM lorry_profiles WHERE lorry_id" in sql:
            return QueryResult(self.lorry)
        if "FROM order_box_requirements r" in sql:
            return QueryResult(rows=self.required_rows)
        return QueryResult()


def test_save_refuses_incomplete_stale_preview_before_any_insert(monkeypatch):
    truck = {"lorry_id": 4, "plate_number": "TEST", "internal_length": 200.0,
             "internal_width": 100.0, "internal_height": 100.0, "max_weight": 1000.0,
             "status": "Available"}
    required = [{"order_id": 10, "box_profile_id": 2, "box_instance": i,
                 "length": 50.0, "width": 40.0, "height": 30.0,
                 "loaded_weight": 20.0} for i in (1, 2)]
    result = generate_plan(truck, required)
    assert result["success"]
    result["placements"].pop()
    result["lorry"] = truck
    result["order_ids"] = [10]
    result["collection_point_id"] = 1

    conn = SaveConnection(truck, [{"order_id": 10, "box_profile_id": 2, "quantity": 2,
                                   "loaded_weight_per_box": 20.0, "box_name": "50L",
                                   "capacity_litre": 50, "length": 50.0, "width": 40.0,
                                   "height": 30.0, "customer_name": "Test Customer"}])

    @contextmanager
    def fake_session():
        yield conn

    monkeypatch.setattr(optimization_service, "db_session", fake_session)
    ok, message, plan_id = optimization_service.save_optimization(result, created_by=1)
    assert not ok
    assert "incomplete" in message.lower() or "missing" in message.lower()
    assert plan_id is None
    assert not any("INSERT INTO loading_plans" in sql for sql, _ in conn.calls)
