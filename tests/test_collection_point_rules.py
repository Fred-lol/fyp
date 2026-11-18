from unittest.mock import patch

from services.collection_point_service import (
    is_lorry_delivery_collection_point,
    list_lorry_delivery_collection_points,
)


def test_perlis_pickup_point_is_not_a_lorry_destination():
    assert not is_lorry_delivery_collection_point(
        {"point_name": "LKIM Fisheries Complex Kuala Perlis", "state": "Perlis"}
    )
    assert is_lorry_delivery_collection_point(
        {"point_name": "LKIM Fisheries Port Kuala Kedah", "state": "Kedah"}
    )
    assert not is_lorry_delivery_collection_point(
        {"point_name": "LKIM Fisheries Complex Kuala Perlis", "state": ""}
    )


def test_lorry_destination_list_excludes_every_perlis_pickup_point():
    points = [
        {"point_name": "LKIM Fisheries Complex Kuala Perlis", "state": "Perlis"},
        {"point_name": "Legacy Kangar Pickup", "state": "Perlis"},
        {"point_name": "LKIM Fisheries Complex Lumut", "state": "Perak"},
    ]
    with patch("services.collection_point_service.list_collection_points", return_value=points):
        assert list_lorry_delivery_collection_points() == [points[2]]
