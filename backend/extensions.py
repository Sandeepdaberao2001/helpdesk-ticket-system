from pymongo import MongoClient

from backend.config import Config

# One MongoClient for the whole app (thread-safe)
_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
db = _client[Config.MONGO_DB_NAME]

users_col    = db["users"]
tickets_col  = db["tickets"]
comments_col = db["comments"]

def create_indexes():
    users_col.create_index("email",     unique=True)
    users_col.create_index("username",  unique=True)
    tickets_col.create_index("created_by")
    tickets_col.create_index("status")
    tickets_col.create_index("assigned_to")
    comments_col.create_index("ticket_id")
    print("MongoDB indexes ready.")
