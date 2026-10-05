import os
from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING


class Database:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise RuntimeError("MONGO_URI is missing")

        self.client = MongoClient(uri)
        self.db = self.client[os.getenv("MONGO_DB", "link_bypass_bot")]

        self.users = self.db.users
        self.bans = self.db.bans
        self.settings = self.db.settings

        self.users.create_index([("user_id", ASCENDING)], unique=True)
        self.bans.create_index([("user_id", ASCENDING)], unique=True)

    @staticmethod
    def now():
        return datetime.now(timezone.utc)

    def add_user(self, user):
        self.users.update_one(
            {"user_id": user.id},
            {"$set": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "updated_at": self.now(),
            }, "$setOnInsert": {
                "user_id": user.id,
                "created_at": self.now(),
            }},
            upsert=True,
        )

    def user_count(self):
        return self.users.count_documents({})

    def is_banned(self, user_id):
        return self.bans.find_one({"user_id": user_id}) is not None

    def ban_user(self, user_id):
        self.bans.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "created_at": self.now()}},
            upsert=True,
        )

    def unban_user(self, user_id):
        self.bans.delete_one({"user_id": user_id})
