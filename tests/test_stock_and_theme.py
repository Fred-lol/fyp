import os
import unittest

import database.db as db
from database.testing import reset_test_database
from services.auth_service import create_user, get_user, update_theme_preference
from services.product_service import add_product, get_product
from services.order_service import place_order, cancel_order
from constants import ROLES


@unittest.skipUnless(os.getenv("AQUALOAD_TEST_DATABASE_URL"), "requires dedicated PostgreSQL test database")
class StockAndThemeTests(unittest.TestCase):
    def setUp(self):
        reset_test_database()

    def tearDown(self):
        pass

    def test_stock_deducts_and_restores_on_cancel(self):
        uid = create_user("Customer", "customer@test.com", "0123456789", "12345678", role=ROLES["CUSTOMER"])
        ok, _ = add_product("Test Fish", "Fish", "", "kg", 10, "Available", updated_by=uid)
        self.assertTrue(ok)
        product = get_product(1)
        ok, _, order_id = place_order(uid, [(product["product_id"], 3)])
        self.assertTrue(ok)
        self.assertEqual(get_product(product["product_id"])["stock_quantity"], 7)
        ok, _ = cancel_order(order_id, uid)
        self.assertTrue(ok)
        self.assertEqual(get_product(product["product_id"])["stock_quantity"], 10)

    def test_theme_preference_is_saved(self):
        uid = create_user("Customer", "theme@test.com", "0123456789", "12345678", role=ROLES["CUSTOMER"])
        ok, _ = update_theme_preference(uid, "Dark")
        self.assertTrue(ok)
        self.assertEqual(get_user(uid)["theme_preference"], "Dark")


if __name__ == "__main__":
    unittest.main()
