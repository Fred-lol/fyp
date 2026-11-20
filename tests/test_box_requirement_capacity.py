import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch

from services import order_service


class BoxRequirementCapacityTests(unittest.TestCase):
    def test_capacity_calculation_insufficient_exact_and_excess(self):
        one_box = [{"capacity_per_box_kg": 250, "quantity": 1}]
        two_boxes = [{"capacity_per_box_kg": 150, "quantity": 2}]
        excess_boxes = [{"capacity_per_box_kg": 200, "quantity": 2}]

        self.assertEqual(order_service.box_requirement_capacity(300, one_box), (250, 50, 0))
        self.assertEqual(order_service.box_requirement_capacity(300, two_boxes), (300, 0, 0))
        self.assertEqual(order_service.box_requirement_capacity(300, excess_boxes), (400, 0, 100))

    def _prepare_save(self, *, inventory=5, capacity=150):
        box = {
            "box_profile_id": 3,
            "box_name": "Test Box",
            "capacity_litre": 50,
            "max_seafood_weight_kg": capacity,
            "length": 60,
            "width": 40,
            "height": 35,
            "status": "Active",
        }
        self.patches = [
            patch.object(order_service, "get_order", return_value={"order_id": 7, "total_weight_kg": 300}),
            patch.object(order_service, "get_box", return_value=box),
            patch.object(order_service, "available_quantity", return_value=inventory),
        ]
        for active_patch in self.patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)
        return box

    def test_save_rejects_insufficient_capacity_before_writing(self):
        self._prepare_save(capacity=250)
        with patch.object(order_service, "db_session") as db_session:
            ok, message = order_service.save_box_combination(
                7, [{"box_profile_id": 3, "quantity": 1, "capacity_per_box_kg": 250}]
            )
        self.assertFalse(ok)
        self.assertIn("50 kg of seafood still requires box capacity", message)
        db_session.assert_not_called()

    def test_save_accepts_exact_capacity_only_after_transaction_commit(self):
        self._prepare_save(capacity=150)
        conn = Mock()

        @contextmanager
        def successful_session():
            yield conn

        with patch.object(order_service, "db_session", successful_session):
            ok, message = order_service.save_box_combination(
                7, [{"box_profile_id": 3, "quantity": 2, "capacity_per_box_kg": 1}]
            )
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirement saved successfully.")
        self.assertEqual(conn.execute.call_count, 2)

    def test_recommendation_success_message_is_returned_only_after_save(self):
        recommendation = {"boxes": [{"box_profile_id": 3, "quantity": 2}]}
        with patch.object(order_service, "recommend_box_combinations", return_value=[recommendation]), \
             patch.object(order_service, "save_box_combination", return_value=(True, "Box requirement saved successfully.")):
            ok, message = order_service.accept_box_recommendation(7)
        self.assertTrue(ok)
        self.assertEqual(message, "Box recommendation accepted and saved successfully.")

    def test_manual_success_message_is_returned_only_after_save(self):
        box = {"box_profile_id": 3, "box_name": "Test Box", "capacity_litre": 50,
               "max_seafood_weight_kg": 150, "length": 60, "width": 40, "height": 35,
               "status": "Active"}
        with patch.object(order_service, "get_order", return_value={"order_id": 7, "total_weight_kg": 300}), \
             patch.object(order_service, "get_box", return_value=box), \
             patch.object(order_service, "save_box_combination", return_value=(True, "Box requirement saved successfully.")):
            ok, message = order_service.set_manual_box_requirements(7, [(3, 2)])
        self.assertTrue(ok)
        self.assertEqual(message, "Manual box requirements saved successfully.")

    def test_save_rejects_unavailable_inventory(self):
        self._prepare_save(inventory=1, capacity=150)
        with patch.object(order_service, "db_session") as db_session:
            ok, message = order_service.save_box_combination(
                7, [{"box_profile_id": 3, "quantity": 2, "capacity_per_box_kg": 150}]
            )
        self.assertFalse(ok)
        self.assertIn("need 2, only 1 available", message)
        db_session.assert_not_called()

    def test_save_does_not_report_success_when_database_commit_fails(self):
        self._prepare_save(capacity=150)

        @contextmanager
        def failed_session():
            yield Mock()
            raise RuntimeError("simulated database failure")

        with patch.object(order_service, "db_session", failed_session):
            ok, message = order_service.save_box_combination(
                7, [{"box_profile_id": 3, "quantity": 2, "capacity_per_box_kg": 150}]
            )
        self.assertFalse(ok)
        self.assertIn("could not be saved", message)


if __name__ == "__main__":
    unittest.main()
