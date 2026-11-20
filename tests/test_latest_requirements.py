import os
import unittest

import database.db as db
from database.testing import reset_test_database
from services.auth_service import create_user
from services.box_service import ensure_box_templates
from services.product_service import add_product
from services.order_service import (
    place_order,
    get_order,
    recommend_box_combinations,
    update_order_status,
    accept_box_recommendation,
    list_customer_orders,
    eligible_orders_for_optimization,
)
from constants import ROLES
from services.optimization_service import build_box_instances


@unittest.skipUnless(os.getenv("AQUALOAD_TEST_DATABASE_URL"), "requires dedicated PostgreSQL test database")
class LatestRequirementTests(unittest.TestCase):
    def setUp(self):
        reset_test_database()
        ensure_box_templates()
        with db.db_session() as conn:
            conn.execute("UPDATE box_profiles SET inventory_quantity=20")
            conn.execute(
                """
                INSERT INTO collection_points(point_name,city,state,postcode,latitude,longitude,status)
                VALUES('Kangar Wholesale Collection Point','Kangar','Perlis','01000',6.4414,100.1986,'Available')
                """
            )
            self.delivery_point_id = conn.execute(
                """
                INSERT INTO collection_points(point_name,city,state,postcode,latitude,longitude,status)
                VALUES('Johor Seafood Collection Point','Johor Bahru','Johor','80000',1.4927,103.7414,'Available')
                """
            ).lastrowid
        self.customer = create_user(
            "Perlis Customer", "perlis@example.com", "0123456789", "12345678",
            role=ROLES["CUSTOMER"], city="Kangar", state="Perlis", postcode="01000",
        )
        self.staff = create_user(
            "Staff", "admin.aquaload@example.com", "0123456790", "12345678",
            role=ROLES["WAREHOUSE_ADMIN"], city="Kangar", state="Perlis", postcode="01000",
        )
        self.delivery_customer = create_user(
            "Johor Customer", "johor@example.com", "0123456791", "12345678",
            role=ROLES["CUSTOMER"], city="Johor Bahru", state="Johor", postcode="80000",
        )
        add_product("Test Snapper", "Fish", "", "kg", 500, "Available", updated_by=self.staff)

    def tearDown(self):
        pass

    def _order(self, kg):
        ok, _, order_id = place_order(self.customer, [(1, kg)])
        self.assertTrue(ok)
        return order_id

    def _delivery_order(self, kg):
        ok, _, order_id = place_order(
            self.delivery_customer, [(1, kg)], collection_point_id=self.delivery_point_id
        )
        self.assertTrue(ok)
        with db.db_session() as conn:
            conn.execute(
                """
                INSERT INTO payments(order_id,customer_id,amount,payment_method,payment_status,transaction_reference)
                VALUES(?,?,?,?,?,?)
                """,
                (order_id, self.delivery_customer, kg * 10, "FPX", "Simulated", f"test-order-{order_id}"),
            )
        ok, message = update_order_status(order_id, "Confirmed", self.staff)
        self.assertTrue(ok, message)
        self.assertEqual(get_order(order_id)["status"], "Confirmed")
        return order_id

    def test_perlis_order_is_local_pickup(self):
        order_id = self._order(50)
        order = get_order(order_id)
        self.assertEqual(order["collection_point"], "Kangar Wholesale Collection Point")
        self.assertEqual(order["collection_assignment"], "Local Pickup")

    def test_50kg_recommends_one_50l_box(self):
        order_id = self._order(50)
        rec = recommend_box_combinations(order_id, 3)[0]
        self.assertEqual(rec["box_count"], 1)
        self.assertEqual(rec["boxes"][0]["capacity_litre"], 50)
        self.assertEqual(rec["boxes"][0]["quantity"], 1)

    def test_100kg_recommends_one_100l_before_two_50l(self):
        order_id = self._order(100)
        recs = recommend_box_combinations(order_id, 3)
        self.assertEqual(recs[0]["box_count"], 1)
        self.assertEqual(recs[0]["boxes"][0]["capacity_litre"], 100)
        alternatives = [
            sorted((b["capacity_litre"], b["quantity"]) for b in r["boxes"])
            for r in recs[1:]
        ]
        self.assertIn([(50, 2)], alternatives)

    def test_status_does_not_skip_operational_stage(self):
        order_id = self._delivery_order(50)
        ok, _ = update_order_status(order_id, "Loaded", self.staff)
        self.assertFalse(ok)
        ok, message = update_order_status(order_id, "Ready for Loading", self.staff)
        self.assertFalse(ok)
        self.assertIn("Save sufficient box requirements first", message)
        self.assertEqual(get_order(order_id)["status"], "Confirmed")
        ok, message = accept_box_recommendation(order_id, 0, self.staff)
        self.assertTrue(ok)
        self.assertEqual(message, "Box requirements saved successfully. Order is now Ready for Loading.")
        order = get_order(order_id)
        self.assertEqual(order["status"], "Ready for Loading")
        self.assertEqual(sum(h["status"] == "Ready for Loading" for h in order["history"]), 1)
        eligible = eligible_orders_for_optimization(self.delivery_point_id)
        self.assertIn(order_id, {entry["order_id"] for entry in eligible})


    def test_box_labels_are_unique_per_order_and_include_customer(self):
        order_id = self._delivery_order(150)
        ok, _ = accept_box_recommendation(order_id, 0, self.staff)
        self.assertTrue(ok)
        boxes = build_box_instances([order_id])
        labels = [b["box_label"] for b in boxes]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(labels, [f"O{order_id}-B{i:02d}" for i in range(1, len(labels) + 1)])
        self.assertTrue(all(b["customer_name"] == "Johor Customer" for b in boxes))

    def test_my_orders_filters_accept_second_argument_and_filter_correctly(self):
        active_id = self._order(10)
        completed_id = self._delivery_order(20)
        cancelled_id = self._order(30)

        ok, _ = accept_box_recommendation(completed_id, 0, self.staff)
        self.assertTrue(ok)
        ok, _ = update_order_status(completed_id, "Loaded", self.staff)
        self.assertTrue(ok)
        ok, _ = update_order_status(completed_id, "Completed", self.staff)
        self.assertTrue(ok)

        ok, _ = update_order_status(cancelled_id, "Cancelled", self.staff)
        self.assertTrue(ok)

        all_ids = {row["order_id"] for row in list_customer_orders(self.customer, "All")}
        active_ids = {row["order_id"] for row in list_customer_orders(self.customer, "Active")}
        completed_ids = {row["order_id"] for row in list_customer_orders(self.customer, "Completed")}
        cancelled_ids = {row["order_id"] for row in list_customer_orders(self.customer, "Cancelled")}

        self.assertTrue({active_id, completed_id, cancelled_id}.issubset(all_ids))
        self.assertIn(active_id, active_ids)
        self.assertNotIn(completed_id, active_ids)
        self.assertNotIn(cancelled_id, active_ids)
        self.assertIn(completed_id, completed_ids)
        self.assertIn(cancelled_id, cancelled_ids)


if __name__ == "__main__":
    unittest.main()
