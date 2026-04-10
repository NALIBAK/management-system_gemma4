"""
app/utils/response.py — Standard API response helpers
======================================================
FIX APPLIED: Added _serialize() to handle types that Flask's jsonify cannot
serialize by default:
  - datetime.timedelta  → converted to str (e.g., "1:30:00")
  - decimal.Decimal     → converted to float

This was needed because MySQL returns TIME columns as timedelta objects and
DECIMAL columns as Decimal objects. Without this, any endpoint touching
period_definition (timetable/attendance) would throw a 500 error, which in turn
caused the browser to treat it as a CORS failure (since error responses don't
always include Access-Control-Allow-Origin headers).

All success() and error() responses run data through _serialize() before
serializing to JSON.
"""
from flask import jsonify
import datetime
from decimal import Decimal


def _serialize(obj):
    """Recursively convert non-JSON-serializable types to serializable ones."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(i) for i in obj]
    elif isinstance(obj, datetime.timedelta):
        # MySQL TIME columns come back as timedelta — convert to "HH:MM:SS" string
        return str(obj)
    elif isinstance(obj, Decimal):
        # MySQL DECIMAL columns come back as Decimal — convert to float
        return float(obj)
    return obj


def success(data=None, message="Success", status=200):
    """Return a standard success JSON response."""
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = _serialize(data)
    return jsonify(resp), status


def error(message="An error occurred", status=400, errors=None):
    """Return a standard error JSON response."""
    resp = {"success": False, "message": message}
    if errors:
        resp["errors"] = _serialize(errors)
    return jsonify(resp), status


def paginate(items, total, page, per_page):
    """Return a pagination metadata wrapper."""
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    }
