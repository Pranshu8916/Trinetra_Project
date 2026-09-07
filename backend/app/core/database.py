from pymongo import AsyncMongoClient

from app.core.config import settings


client = AsyncMongoClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)

database = client[settings.mongodb_database]

