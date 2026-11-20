from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


PRODUCT = {
    "product_id": 31,
    "product_name": "Test Mackerel",
    "category": "Fish",
    "description": "A detailed seafood description for catalogue testing.",
    "unit": "kg",
    "unit_price": 21.5,
    "stock_quantity": 60.0,
    "availability_status": "Available",
}


@pytest.fixture
def catalogue_app(monkeypatch):
    import bootstrap
    import components.navigation as navigation
    import services.favorites_service as favorites
    import services.order_service as orders
    import services.payment_service as payments
    import services.product_service as products

    customer_favorites = set()
    monkeypatch.setattr(bootstrap, "bootstrap_app", lambda: None)
    monkeypatch.setattr(navigation, "customer_sidebar", lambda: None)
    monkeypatch.setattr(navigation, "require_role", lambda *roles: None)
    monkeypatch.setattr(orders, "list_products", lambda *args: [dict(PRODUCT)])
    monkeypatch.setattr(orders, "product_categories", lambda: ["Fish"])
    monkeypatch.setattr(products, "get_product", lambda product_id: dict(PRODUCT) if int(product_id) == 31 else None)
    monkeypatch.setattr(favorites, "list_favorite_product_ids", lambda customer_id: set(customer_favorites))

    def set_favorite(customer_id, product_id, enabled):
        if enabled:
            customer_favorites.add(int(product_id))
        else:
            customer_favorites.discard(int(product_id))
        return True, "Favorite saved." if enabled else "Removed from favorites."

    monkeypatch.setattr(favorites, "set_favorite", set_favorite)

    def summary(items):
        lines = []
        for product_id, quantity in items:
            if int(product_id) == PRODUCT["product_id"]:
                lines.append({
                    **PRODUCT,
                    "quantity": float(quantity),
                    "line_total": float(quantity) * PRODUCT["unit_price"],
                })
        return {
            "items": lines,
            "total_weight_kg": sum(line["quantity"] for line in lines),
            "total_amount": sum(line["line_total"] for line in lines),
        }

    monkeypatch.setattr(payments, "checkout_summary", summary)
    app = AppTest.from_file(Path("pages/order_seafood.py").resolve())
    app.session_state["logged_in"] = True
    app.session_state["user_id"] = 8
    app.session_state["user_role"] = "Customer"
    app.session_state["cart"] = {}
    return app, customer_favorites


def test_view_details_opens_product_without_losing_customer_session(catalogue_app):
    app, _ = catalogue_app
    app.run()
    assert not app.exception
    assert len([button for button in app.button if button.label == "View Details"]) == 1
    assert not any(button.key == "product_image_31" for button in app.button)
    app.button(key="view_details_31").click().run()
    assert not app.exception
    assert app.session_state["logged_in"] is True
    assert app.session_state["user_id"] == 8
    assert app.session_state["user_role"] == "Customer"
    assert app.session_state["selected_seafood_id"] == 31
    assert app.button(key="back_to_catalogue")
    assert any(element.label == "Quantity (kg)" for element in app.number_input)


def test_favorite_persists_and_add_to_cart_returns_to_catalogue(catalogue_app):
    app, favorite_ids = catalogue_app
    app.run()
    filter_button = app.button(key="catalogue_favorites_filter")
    assert filter_button.label == "Favorites"
    assert filter_button.help == "Show only your saved favorites"
    app.text_input(key="catalogue_search").set_value("Mackerel").run()
    app.selectbox(key="catalogue_category").set_value("Fish").run()
    assert app.button(key="favorite_31").help == "Add to favorites"
    app.button(key="favorite_31").click().run()
    assert not app.exception
    assert favorite_ids == {31}
    assert app.session_state["favorite_product_ids"] == {31}

    app.button(key="catalogue_favorites_filter").click().run()
    assert app.session_state["catalogue_favorites_only"] is True
    assert app.button(key="catalogue_favorites_filter").label == "Favorites Only"
    assert app.session_state["catalogue_search"] == "Mackerel"
    assert app.session_state["catalogue_category"] == "Fish"
    assert len([button for button in app.button if button.label == "View Details"]) == 1

    app.button(key="view_details_31").click().run()
    assert app.session_state["selected_seafood_id"] == 31
    detail_favorite = app.button(key="detail_favorite")
    assert detail_favorite.label == ""
    assert detail_favorite.help == "Remove from favorites"
    app.button(key="detail_add_to_cart").click().run()
    assert not app.exception
    assert app.session_state.get("selected_seafood_id") is None
    assert app.session_state["cart"] == {31: 10}
    assert app.session_state["logged_in"] is True


def test_detail_favorite_icon_toggles_and_stays_synchronized(catalogue_app):
    app, favorite_ids = catalogue_app
    app.run()
    app.button(key="view_details_31").click().run()

    favorite_button = app.button(key="detail_favorite")
    assert favorite_button.label == ""
    assert favorite_button.icon == ":material/favorite_border:"
    assert favorite_button.help == "Add to favorites"
    favorite_button.click().run()
    assert favorite_ids == {31}
    favorite_button = app.button(key="detail_favorite")
    assert favorite_button.icon == ":material/favorite:"
    assert favorite_button.help == "Remove from favorites"

    app.button(key="back_to_catalogue").click().run()
    assert app.button(key="favorite_31").help == "Remove from favorites"
