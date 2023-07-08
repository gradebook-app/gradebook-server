from pymongo import MongoClient
from config.config import config


def connect_db():
    mongo_uri = config["mongodb"]["uri"]
    mongo_db = config["mongodb"]["db"]
    mongo_client = MongoClient(mongo_uri)
    return mongo_client.get_database(mongo_db)


db = connect_db()
