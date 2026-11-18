import os
import unittest
from uuid import uuid4

import database.db as db
from database.testing import reset_test_database
from services.auth_service import create_user
from services.product_service import add_product
from services.payment_service import complete_demo_payment, get_payment
from services.order_service import get_order
from constants import ROLES


@unittest.skipUnless(os.getenv("AQUALOAD_TEST_DATABASE_URL"), "requires dedicated PostgreSQL test database")
class PaymentUITests(unittest.TestCase):
    def setUp(self):
        reset_test_database()
        self.customer = create_user(
            "Payment Customer",
            "pay@example.com",
            "0123456789",
            "12345678",
            role=ROLES["CUSTOMER"],
            city="Kangar",
            state="Perlis",
            postcode="01000",
        )
        with db.db_session() as conn:
            conn.execute(
                """
                INSERT INTO collection_points(point_name,city,state,postcode,latitude,longitude,status)
                VALUES('Kangar Wholesale Collection Point','Kangar','Perlis','01000',6.4414,100.1986,'Available')
                """
            )
        add_product(
            "Payment Fish",
            "Fish",
            "",
            "kg",
            100,
            "Available",
            updated_by=self.customer,
            unit_price=20.0,
        )

    def tearDown(self):
        pass

    def test_demo_payment_creates_paid_perlis_pickup_order(self):
        ok, _, order_id = complete_demo_payment(
            self.customer,
            [(1, 10)],
            "Online Banking (FPX)",
            {"bank": "Maybank2u", "demo_confirmed": True},
            collection_point_id=1,
            submission_key=str(uuid4()),
        )
        self.assertTrue(ok)
        order = get_order(order_id, self.customer)
        payment = get_payment(order_id)
        self.assertEqual(order["status"], "Pending")
        self.assertEqual(order["collection_assignment"], "Local Pickup")
        self.assertEqual(payment["payment_status"], "Simulated")
        self.assertEqual(payment["amount"], 200.0)


if __name__ == "__main__":
    unittest.main()
