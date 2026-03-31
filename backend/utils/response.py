from flask import jsonify


def success(data=None, message="OK", status=200):
    """
    Standard success envelope:
    { "success": true, "message": "...", "data": {...} }
    """
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def error(message="Something went wrong", status=400, errors=None):
    """
    Standard error envelope:
    { "success": false, "message": "...", "errors": [...] }
    """
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status