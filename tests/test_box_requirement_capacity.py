import unittest
from contextlib import contextmanager
from unittest.mock import patch

from services import order_service


class _Result:
    def __init__(self, row=None, rowcount=1):
        self.row = row
        self.rowcount = rowcount

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, *, weight=300, capacity=150, inventory=5, reserved=0, status="Confirmed"):
        self.weight = weight
        self.capacity = capacity
        self.inventory = inventory
        self.reserved = reserved
        self.status = status
        self.history = []
        self.requirements = []
        self.statements = []

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        params = params or ()
        self.statements.append((normalized, params))
        if normalized.startswith("SELECT * FROM seafood_orders"):
            return _Result({
                "order_id": 7,
                "status": self.status,
                "archived_at": None,
                "collection_assignment": "Customer Selected",
                "collection_point_id": 2,
            })
        if normalized.startswith("SELECT payment_status FROM payments"):
            return _Result({"payment_status": "Simulated"})
        if "SUM(CASE WHEN unit='kg'" in normalized:
            return _Result({"total_weight": self.weight})
        if normalized.startswith("SELECT * FROM box_profiles"):
            return _Result({
                "box_profile_id": 3,
                "box_name": "Test 150 kg Box",
                "capacity_litre": 50,
                "max_seafood_weight_kg": self.capacity,
                "length": 60,
                "width": 40,
                "height": 35,
                "inventory_quantity": self.inventory,
                "status": "Active",
            })
        if "SUM(r.quantity),0) reserved" in normalized:
            return _Result({"reserved": self.reserved})
        if normalized.startswith("UPDATE seafood_orders SET status='Ready for Loading'"):
            if self.status != "Confirmed":
                return _Result(rowcount=0)
            self.status = "Ready for Loading"
            return _Result(rowcount=1)
        if normalized.startswith("SELECT history_id FROM order_status_history"):
            return _Result(next((row for row in self.history if row["status"] == "Ready for Loading"), None))
        if normalized.startswith("INSERT INTO order_status_history"):
            self.history.append({"status": params[1], "updated_by": params[2], "note": params[3]})
            return _Result()
        if normalized.startswith("DELETE FROM order_box_requirements"):
            self.requirements = []
            return _Result()
        if normalized.startswith("INSERT INTO order_box_requirements"):
            self.requirements.append({"order_id": params[0], "box_profile_id": params[1], "quantity": params[2]})
            return _Result()
        return _Result()


class BoxRequirementCapacityTests(unittest.TestCase):
    def test_capacity_calculation_insufficient_exact_and_excess(self):
        self.assertEqual(
            order_service.box_requirement_capacity(300, [{"capacity_per_box_kg": 250, "quantity": 1}]),
            (250, 50, 0),
        )
        self.assertEqual(
            order_service.box_requirement_capacity(300, [{"capacity_per_box_kg": 150, "quantity": 2}]),
            (300, 0, 0),
        )
        self.assertEqual(
            order_service.box_requirement_capacity(300, [{"capacity_per_box_kg": 200, "quantity": 2}]),
            (400, 0, 100),
        )

    def _save_with_connection(self, connection, boxes, *, fail_commit=False, updated_by=9):
        @contextmanager
        def session():
            original_status = connection.status
            original_history = list(connection.history)
            original_requirements = list(connection.requirements)
            try:
                yield connection
                if fail_commit:
                    raise RuntimeError("simulated commit failure")
            except Exception:
                connection.status = original_status
                connection.history = original_history
                connection.requirements = original_requirements
                raise

        with patch.object(order_service, "db_session", session):
            return order_service.save_box_combination(7, boxes, updated_by)

    def test_rejects_insufficient_capacity_without_advancing_order(self):
        connection = _Connection(weight=300, capacity=250)
        ok, message = self._save_with_connection(
            connection, [{"box_profile_id": 3, "quantity": 1}]
        )
        self.assertFalse(ok)
        self.assertIn("50 kg of seafood still requires box capacity", message)
        self.assertEqual(connection.status, "Confirmed")
        self.assertFalse(connection.history)
        self.assertFalse(connection.requirements)

    def test_accepts_exact_capacity_and_saves_status_history_atomically(self):
        connection = _Connection(weight=300, capacity=150)
        ok, message = self._save_with_connection(
            connection, [{"box_profile_id": 3, "quantity": 2}]
        )
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirements saved successfully. Order is now Ready for Loading.")
        self.assertEqual(connection.status, "Ready for Loading")
        self.assertEqual([row["status"] for row in connection.history], ["Ready for Loading"])
        self.assertEqual(len(connection.requirements), 1)

    def test_inventory_shortage_prevents_status_change(self):
        connection = _Connection(weight=300, capacity=150, inventory=1)
        ok, message = self._save_with_connection(
            connection, [{"box_profile_id": 3, "quantity": 2}]
        )
        self.assertFalse(ok)
        self.assertIn("need 2, only 1 available", message)
        self.assertEqual(connection.status, "Confirmed")
        self.assertFalse(connection.history)

    def test_invalid_order_statuses_cannot_be_advanced(self):
        for status in ("Pending", "Loaded", "Completed", "Cancelled"):
            with self.subTest(status=status):
                connection = _Connection(status=status)
                ok, _ = self._save_with_connection(
                    connection, [{"box_profile_id": 3, "quantity": 2}]
                )
                self.assertFalse(ok)
                self.assertEqual(connection.status, status)
                self.assertFalse(connection.history)

    def test_ready_order_box_edit_does_not_duplicate_status_history(self):
        connection = _Connection(status="Ready for Loading")
        connection.history = [{"status": "Ready for Loading", "note": "existing transition"}]
        ok, message = self._save_with_connection(
            connection, [{"box_profile_id": 3, "quantity": 2}]
        )
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirements saved successfully. Order is now Ready for Loading.")
        self.assertEqual(connection.status, "Ready for Loading")
        self.assertEqual(len(connection.history), 1)

    def test_failed_commit_rolls_back_box_assignment_and_status(self):
        connection = _Connection()
        ok, message = self._save_with_connection(
            connection, [{"box_profile_id": 3, "quantity": 2}], fail_commit=True
        )
        self.assertFalse(ok)
        self.assertIn("order status was not advanced", message)
        self.assertEqual(connection.status, "Confirmed")
        self.assertFalse(connection.history)
        self.assertFalse(connection.requirements)

    def test_recommendation_uses_the_success_message_after_save(self):
        rec = {"boxes": [{"box_profile_id": 3, "quantity": 2}]}
        with patch.object(order_service, "recommend_box_combinations", return_value=[rec]), \
             patch.object(order_service, "save_box_combination", return_value=(True, "Box requirements saved successfully. Order is now Ready for Loading.")) as save:
            ok, message = order_service.accept_box_recommendation(7, updated_by=9)
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirements saved successfully. Order is now Ready for Loading.")
        save.assert_called_once_with(7, rec["boxes"], 9)

    def test_manual_assignment_runs_the_same_atomic_save(self):
        connection = _Connection()
        @contextmanager
        def session():
            yield connection
        with patch.object(order_service, "db_session", session):
            ok, message = order_service.set_manual_box_requirements(7, [(3, 2)], updated_by=9)
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirements saved successfully. Order is now Ready for Loading.")
        self.assertEqual(connection.status, "Ready for Loading")
        self.assertEqual(len(connection.history), 1)


if __name__ == "__main__":
    unittest.main()
