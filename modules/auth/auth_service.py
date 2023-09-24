import jwt
from modules.genesis.genesis_service import GenesisService
from config.config import config
from mongo_config import db
from cryptography.fernet import Fernet
from bson import ObjectId, json_util
import time
import datetime


class AuthService:
    def __init__(self):
        self.genesis_service = GenesisService()
        self.fernet = Fernet(config["fernet"]["key"].encode())

    def logout(self, body):
        userId = body["userId"]
        user_modal = db.get_collection("users")
        user_modal.update_one(
            {
                "_id": ObjectId(userId),
            },
            {
                "$set": {
                    "notificationToken": None,
                    "status": "inactive",
                }
            },
        )
        return {}

    async def login(self, email, password, school_district, notificationToken):
        email = email.strip()
        user_modal = db.get_collection("users")

        [
            genesisToken,
            userId,
            access,
            studentId,
        ] = await self.genesis_service.get_access_token(
            email, password, school_district
        )
        user = {}

        current_timestamp = datetime.datetime.today().replace(microsecond=0)

        if access:
            encrypted_pass = self.encrypt_password(password)
            doc = user_modal.find_one({"email": email})
            if doc == None:
                inserted_doc = user_modal.insert_one(
                    {
                        "email": email,
                        "status": "active",
                        "pass": encrypted_pass,
                        "studentId": studentId,
                        "schoolDistrict": school_district,
                        "notificationToken": notificationToken,
                        "unweightedGPA": None,
                        "pastGPA": None,
                        "weightedGPA": None,
                        "createdAt": current_timestamp,
                        "loggedInAt": current_timestamp,
                    }
                )
                mongoUserId = inserted_doc.inserted_id
            elif isinstance(doc, dict):
                updated_doc = user_modal.find_one_and_update(
                    {"email": email},
                    {
                        "$set": {
                            "loggedInAt": current_timestamp,
                            "status": "active",
                            "pass": encrypted_pass,
                            "notificationToken": notificationToken,
                        }
                    },
                )

                mongoUserId = ObjectId(updated_doc["_id"])
            year = datetime.datetime.now().year
            month = datetime.datetime.now().month
            time_to_query = f"01/09/{year}" if 9 <= month <= 12 else f"01/09/{year - 1}"
            time_in_seconds = time.mktime(
                datetime.datetime.strptime(time_to_query, "%d/%m/%Y").timetuple()
            )

            user = user_modal.aggregate(
                [
                    {
                        "$match": {"_id": mongoUserId},
                    },
                    {
                        "$lookup": {
                            "from": "gpa-history",
                            "let": {"userId": "$_id"},
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$and": [
                                                {"$eq": ["$userId", "$$userId"]},
                                                {
                                                    "$gte": [
                                                        "$timestamp",
                                                        time_in_seconds,
                                                    ]
                                                },
                                            ]
                                        }
                                    }
                                }
                            ],
                            "as": "gpaHistory",
                        }
                    },
                    {
                        "$addFields": {
                            "_id": {
                                "$toString": "$_id",
                            }
                        }
                    },
                ]
            )

            user = user.next()

            data = {
                "token": genesisToken,
                "email": userId,
                "schoolDistrict": school_district,
                "userId": str(mongoUserId),
                "studentId": studentId,
            }
            accessToken = self.create_token(data)

            user["createdAt"] = str(user["createdAt"])
            user["loggedInAt"] = str(user["loggedInAt"])

            response = {
                "accessToken": accessToken,
                "user": user if user else {},
                "access": access,
            }
            return json_util.dumps(response)
        else:
            return {"access": False}

    def encrypt_password(self, text):
        encrypted_credential = self.fernet.encrypt(text.encode())
        return encrypted_credential.decode()

    def dyscrypt_password(self, password):
        dycrypted_password = self.fernet.decrypt(password.encode())
        return dycrypted_password

    def create_token(self, data):
        jwt_token = config["jwt"]["token"]
        access_token = jwt.encode(data, jwt_token, algorithm="HS256")
        return access_token
