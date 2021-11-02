from pymongo import MongoClient
from config.config import config

mongo_uri = config["mongodb"]["uri"]
mongo_db = config["mongodb"]["db"]

mongo_client = MongoClient(mongo_uri)
db = mongo_client.get_database(mongo_db)