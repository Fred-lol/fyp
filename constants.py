ROLES = {
    "CUSTOMER": "Customer",
    "WAREHOUSE_ADMIN": "Warehouse Administrator",
    "LOADING_SUPERVISOR": "Loading Supervisor",
    "SEAFOOD_SUPPLIER": "Seafood Supplier",
}

# All staff roles intentionally share the same AquaLoad operational functions.
STAFF_ROLES = {
    ROLES["WAREHOUSE_ADMIN"],
    ROLES["LOADING_SUPERVISOR"],
    ROLES["SEAFOOD_SUPPLIER"],
}

USER_STATUSES = ["Active", "Inactive"]
LORRY_STATUSES = ["Available", "In Transit", "Unavailable"]
BOX_STATUSES = ["Active", "Inactive"]
PRODUCT_STATUSES = ["Available", "Unavailable"]
THEME_PREFERENCES = ["System", "Light", "Dark"]
LOW_STOCK_THRESHOLD = 10.0
MIN_WHOLESALE_ORDER_KG = 10.0

# Controlled seafood data prevents inconsistent free-text categories.
SEAFOOD_CATEGORIES = [
    "Fish",
    "Crustaceans (Prawn, Crab & Lobster)",
    "Molluscs & Shellfish (Cockle, Clam, Mussel & Oyster)",
    "Cephalopods (Squid, Cuttlefish & Octopus)",
    "Seaweed",
    "Other Seafood",
]

# AquaLoad currently standardises seafood order quantities in kilograms so that
# order weight, box recommendation and lorry weight calculations use one unit.
SEAFOOD_UNITS = ["kg"]

MALAYSIA_STATES = [
    "Johor",
    "Kedah",
    "Kelantan",
    "Melaka",
    "Negeri Sembilan",
    "Pahang",
    "Perak",
    "Perlis",
    "Pulau Pinang",
    "Selangor",
    "Terengganu",
    "W.P. Kuala Lumpur",
    "W.P. Putrajaya",
]

# Staff updates operational statuses manually. Only Pending is created
# automatically when the Customer places an order.
ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Ready for Pickup",
    "Ready for Loading",
    "Loaded",
    "Completed",
    "Cancelled",
]

ORDER_STATUS_TRANSITIONS = {
    "Pending": ["Confirmed", "Cancelled"],
    "Confirmed": ["Ready for Pickup", "Ready for Loading", "Cancelled"],
    "Ready for Pickup": ["Completed", "Cancelled"],
    "Ready for Loading": ["Loaded", "Cancelled"],
    "Loaded": ["Completed"],
    "Completed": [],
    "Cancelled": [],
}

EDITABLE_ORDER_STATUSES = {"Pending"}
# A customer may cancel until the seafood has been loaded for delivery.
CANCELLABLE_ORDER_STATUSES = {"Pending", "Confirmed", "Ready for Pickup", "Ready for Loading"}
OPTIMIZATION_ELIGIBLE_STATUSES = {"Ready for Loading"}

# Fixed box templates. Staff selects a template and manages quantity instead of
# typing different dimensions for the same nominal box size.
BOX_TEMPLATE_DEFAULTS = [
    {
        "box_name": "35L Insulated Box",
        "capacity_litre": 35,
        "length": 51.0,
        "width": 34.5,
        "height": 34.0,
        "max_seafood_weight_kg": 35.0,
    },
    {
        "box_name": "50L Insulated Box",
        "capacity_litre": 50,
        "length": 67.5,
        "width": 40.5,
        "height": 36.0,
        "max_seafood_weight_kg": 50.0,
    },
    {
        "box_name": "75L Insulated Box",
        "capacity_litre": 75,
        "length": 72.0,
        "width": 48.5,
        "height": 38.5,
        "max_seafood_weight_kg": 75.0,
    },
    {
        "box_name": "100L Insulated Box",
        "capacity_litre": 100,
        "length": 82.5,
        "width": 50.0,
        "height": 41.0,
        "max_seafood_weight_kg": 100.0,
    },
]
