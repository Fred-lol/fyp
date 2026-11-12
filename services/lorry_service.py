import re

from constants import LORRY_STATUSES
from database.db import db_session
from database.schema import initialize_schema

# Standard Malaysian civilian registration series, for example B 1234,
# VAB 1234, WXX 1234 A, or VBB 1234 AB. Spaces and hyphens are cosmetic.
MALAYSIAN_PLATE_PATTERN = re.compile(r"[A-Z]{1,3}\d{1,4}[A-Z]{0,3}")
MALAYSIAN_PLATE_MIN_LENGTH = 2
MALAYSIAN_PLATE_MAX_LENGTH = 10
# JPJ special-number series can use a longer word index, e.g. MALAYSIA 1,
# PUTRAJAYA 1, or M_M 1. Diplomatic/international registrations are numeric
# groups ending in DC, CC, UN, or PA (e.g. 14-07-UN).
MALAYSIAN_SPECIAL_SERIES_PATTERN = re.compile(r"[A-Z][A-Z_]{1,11}\d{1,4}[A-Z]{0,3}")
MALAYSIAN_DIPLOMATIC_PATTERN = re.compile(r"\d{4,6}(?:DC|CC|UN|PA)")
MALAYSIAN_SPECIAL_PLATE_MAX_LENGTH = 15

# Cargo-space safeguards for standard Malaysian rigid goods lorries. The
# vehicle's JPJ registration remains the final legal specification.
MALAYSIA_LORRY_LIMITS = {
    "length": (200.0, 1220.0),
    "width": (120.0, 250.0),
    "height": (120.0, 420.0),
    "weight": (500.0, 38000.0),
}


def is_valid_lorry_configuration(lorry):
    """Whether a stored lorry can safely be used for loading optimisation."""
    try:
        values = {
            "length": float(lorry["internal_length"]),
            "width": float(lorry["internal_width"]),
            "height": float(lorry["internal_height"]),
            "weight": float(lorry["max_weight"]),
        }
    except (KeyError, TypeError, ValueError):
        return False
    return all(
        MALAYSIA_LORRY_LIMITS[field][0] <= value <= MALAYSIA_LORRY_LIMITS[field][1]
        for field, value in values.items()
    )


def normalise_malaysian_plate(value):
    """Return a database-safe Malaysian plate or a clear validation message."""
    plate = re.sub(r"[\s-]+", "", str(value or "").upper())
    if not plate:
        return None, "Enter the lorry plate number."
    if len(plate) < MALAYSIAN_PLATE_MIN_LENGTH:
        return None, "Plate number is too short. Use at least 1 letter followed by 1 digit, for example B 1."
    if len(plate) > MALAYSIAN_SPECIAL_PLATE_MAX_LENGTH:
        return None, "Plate number is too long. Standard plates allow up to 10 characters; recognised special series allow up to 15 characters."
    is_standard = len(plate) <= MALAYSIAN_PLATE_MAX_LENGTH and MALAYSIAN_PLATE_PATTERN.fullmatch(plate)
    is_special_series = MALAYSIAN_SPECIAL_SERIES_PATTERN.fullmatch(plate)
    is_diplomatic = MALAYSIAN_DIPLOMATIC_PATTERN.fullmatch(plate)
    if not (is_standard or is_special_series or is_diplomatic):
        return None, (
            "Use a standard Malaysian format (VAB 1234), an official special series "
            "(MALAYSIA 1 or M_M 1), or a diplomatic/international format (14-07-UN)."
        )
    return plate, None


def list_lorries(status="All", search=""):
    initialize_schema()
    sql = "SELECT * FROM lorry_profiles WHERE 1=1"
    params = []
    if status != "All":
        sql += " AND status=?"; params.append(status)
    if search.strip():
        sql += " AND LOWER(plate_number) LIKE ?"; params.append(f"%{search.strip().lower()}%")
    sql += " ORDER BY plate_number"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_lorry(lorry_id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM lorry_profiles WHERE lorry_id=?", (lorry_id,)).fetchone()
    return dict(row) if row else None


def save_lorry(plate_number, length, width, height, max_weight, status, lorry_id=None):
    plate_number, plate_error = normalise_malaysian_plate(plate_number)
    if plate_error:
        return False, plate_error
    try:
        length, width, height, max_weight = map(float, (length, width, height, max_weight))
    except (TypeError, ValueError):
        return False, "Dimensions and maximum weight must be valid numbers."
    for value, field in ((length, "length"), (width, "width"), (height, "height"), (max_weight, "weight")):
        minimum, maximum = MALAYSIA_LORRY_LIMITS[field]
        if value < minimum or value > maximum:
            unit = "kg" if field == "weight" else "cm"
            label = "Maximum load weight" if field == "weight" else f"Internal {field}"
            return False, f"{label} must be between {minimum:g} {unit} and {maximum:,.0f} {unit}."
    if status not in LORRY_STATUSES:
        return False, "Select a valid lorry status."
    try:
        with db_session() as conn:
            if lorry_id:
                conn.execute("UPDATE lorry_profiles SET plate_number=?,internal_length=?,internal_width=?,internal_height=?,max_weight=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE lorry_id=?", (plate_number,length,width,height,max_weight,status,lorry_id))
            else:
                conn.execute("INSERT INTO lorry_profiles(plate_number,internal_length,internal_width,internal_height,max_weight,status) VALUES(?,?,?,?,?,?)", (plate_number,length,width,height,max_weight,status))
        return True, "Lorry profile saved successfully."
    except Exception as exc:
        if "unique" in str(exc).lower() and "plate" in str(exc).lower():
            return False, "A lorry with this plate number already exists."
        return False, "Unable to save lorry profile."


def set_lorry_status(lorry_id, status):
    """Update availability only; lorry registration and capacity remain immutable."""
    if status not in LORRY_STATUSES:
        return False, "Select a valid lorry status."
    with db_session() as conn:
        result = conn.execute(
            "UPDATE lorry_profiles SET status=?, updated_at=CURRENT_TIMESTAMP WHERE lorry_id=?",
            (status, lorry_id),
        )
    if result.rowcount == 0:
        return False, "Lorry profile could not be found."
    return True, "Lorry status updated successfully."


def delete_lorry(lorry_id):
    try:
        with db_session() as conn:
            conn.execute("DELETE FROM lorry_profiles WHERE lorry_id=?", (lorry_id,))
        return True, "Lorry profile deleted."
    except Exception:
        return False, "This lorry is already used by a loading plan and cannot be deleted. Set it to Unavailable instead."
