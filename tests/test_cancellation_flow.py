from contextlib import contextmanager

from services import order_service
from pathlib import Path
from streamlit.testing.v1 import AppTest


class CancellationConnection:
    def __init__(self):
        self.status = "Pending"
        self.payment_status = "Simulated"
        self.history = []
        self.stock_restores = 0

    def execute(self, sql, params=()):
        sql = sql.strip()
        if sql.startswith("SELECT status FROM seafood_orders"):
            return Row({"status": self.status})
        if sql.startswith("SELECT * FROM seafood_orders"):
            return Row({"status": self.status, "collection_assignment": "Customer Selected"})
        if sql.startswith("UPDATE seafood_orders"):
            self.status = "Cancelled"
        if sql.startswith("UPDATE payments"):
            self.payment_status = "Demo Refund Pending"
        if sql.startswith("INSERT INTO order_status_history"):
            self.history.append(params)
        return Row(None)


class Row:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return self.value


def test_customer_cancel_is_atomic_and_does_not_duplicate_notice(monkeypatch):
    conn = CancellationConnection()

    @contextmanager
    def session():
        yield conn

    monkeypatch.setattr(order_service, "db_session", session)
    monkeypatch.setattr(order_service, "_restore_order_stock", lambda *args: setattr(conn, "stock_restores", conn.stock_restores + 1))
    assert order_service.cancel_order(1, 2)[0]
    assert not order_service.cancel_order(1, 2)[0]
    assert conn.status == "Cancelled" and conn.payment_status == "Demo Refund Pending"
    assert conn.stock_restores == 1 and len(conn.history) == 1
    assert conn.history[0][3] == order_service.cancellation_customer_message()


def test_staff_cancel_persists_customer_notice_once(monkeypatch):
    conn = CancellationConnection()

    @contextmanager
    def session():
        yield conn

    monkeypatch.setattr(order_service, "db_session", session)
    monkeypatch.setattr(order_service, "_restore_order_stock", lambda *args: setattr(conn, "stock_restores", conn.stock_restores + 1))
    assert order_service.update_order_status(1, "Cancelled", 9)[0]
    assert not order_service.update_order_status(1, "Cancelled", 9)[0]
    assert conn.status == "Cancelled" and conn.payment_status == "Demo Refund Pending"
    assert conn.stock_restores == 1 and len(conn.history) == 1
    assert conn.history[0][3] == order_service.cancellation_customer_message(by_staff=True)


def test_staff_cancellation_notice_remains_in_customer_orders_after_rerun(monkeypatch):
    import bootstrap
    import components.navigation as navigation

    monkeypatch.setattr(bootstrap, "bootstrap_app", lambda: None)
    monkeypatch.setattr(navigation, "customer_sidebar", lambda: None)
    order = {
        "order_id": 1, "status": "Cancelled", "total_weight_kg": 10,
        "payment_status": "Demo Refund Pending",
    }
    detail = {
        **order, "collection_point": "LKIM Kuala Perlis", "total_amount": 200,
        "collection_assignment": "Customer Selected", "items": [],
        "payment": {"payment_status": "Demo Refund Pending", "amount": 200},
        "history": [{"status": "Cancelled", "updated_by": 9,
                     "note": order_service.cancellation_customer_message(by_staff=True)}],
    }
    monkeypatch.setattr(order_service, "list_customer_orders", lambda customer_id, view_filter: [order])
    monkeypatch.setattr(order_service, "get_order", lambda order_id, customer_id: detail)
    app = AppTest.from_file(Path("pages/my_orders.py").resolve())
    app.session_state["user_id"] = 2
    for _ in range(2):
        app.run()
        assert not app.exception
        assert any(
            order_service.cancellation_customer_message(by_staff=True) in message.value
            for message in app.info
        )


def test_archived_cancelled_orders_remain_queryable_for_customer_notice(monkeypatch):
    queries = []

    class Results:
        def fetchall(self):
            return []

    class CaptureConnection:
        def execute(self, sql, params=()):
            queries.append((sql, params))
            return Results()

    @contextmanager
    def session():
        yield CaptureConnection()

    monkeypatch.setattr(order_service, "archive_expired_completed_orders", lambda: None)
    monkeypatch.setattr(order_service, "db_session", session)
    order_service.list_customer_orders(2, "Cancelled")
    assert "o.archived_at IS NULL OR o.status='Cancelled'" in queries[0][0]
    assert queries[0][1] == (2,)
