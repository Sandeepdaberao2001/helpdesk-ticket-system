from bson import ObjectId
from datetime import datetime


def serialize(doc: dict) -> dict:
    """
    Converts a raw MongoDB document into a JSON-serializable dict.
    - ObjectId  -> string  (e.g. "664abc...")
    - datetime  -> ISO string (e.g. "2024-06-01T10:30:00")
    """
    if doc is None:
        return None

    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["id"] = str(value)          # rename _id -> id for React
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value

    return result


def serialize_list(docs: list) -> list:
    """Serialize a list of MongoDB documents."""
    return [serialize(doc) for doc in docs]


def to_object_id(id_str: str):
    """
    Safely convert a string to ObjectId.
    Returns None if the string is not a valid ObjectId.
    """
    try:
        return ObjectId(id_str)
    except Exception:
        return None
