import json
import jwt
from modules.genesis.genesis_service import GenesisService
from config.config import config
from mongo_config import db
from cryptography.fernet import Fernet

class AuthService: 
    def __init__(self): 
        self.genesis_service = GenesisService()
        self.fernet = Fernet(config["fernet"]["key"].encode())

    def login(self, email, password, school_district): 
        user_modal = db.get_collection("users")

        [ genesisToken, userId, access ] = self.genesis_service.get_access_token(email, password, school_district)
        mongoUserId = str()

        user = None

        if access: 
            encrypted_pass = self.encrypt_password(password) 
            doc = user_modal.find_one({ "email": email })
            if doc == None: 
                inserted_doc = user_modal.insert_one({
                    "email": email,
                    "status": "active",
                    "pass": encrypted_pass,
                    "schoolDistrict": school_district,
                    "notificationToken": None,
                })
                mongoUserId = str(inserted_doc.inserted_id)
                user = inserted_doc
            elif isinstance(doc, dict): 
                updated_doc = user_modal.find_one_and_update(
                    { "email": email }, 
                    { "$set": { 
                            "status": "active",
                            "pass": encrypted_pass
                        }
                    }
                )
                user = updated_doc
                mongoUserId = str(updated_doc["_id"])

        data = { 
            "token": genesisToken, 
            "email": userId, 
            "schoolDistrict":  school_district, 
            "userId": mongoUserId
        }
        accessToken = self.create_token(data)
        response = { 
            "accessToken": accessToken, 
            "user": {
                "_id": str(user["_id"]),
                "notificationToken": user["notificationToken"]
            }, 
            "access": access 
        }
        return json.dumps(response)
    
    def encrypt_password(self, text): 
        encrypted_credential = self.fernet.encrypt(text.encode())
        return encrypted_credential.decode()

    def dyscrypt_password(self, password): 
        dycrypted_password = self.fernet.decrypt(password.encode())
        return dycrypted_password

    def create_token(self, data): 
        jwt_token = config['jwt']['token']
        access_token = jwt.encode(data, jwt_token, algorithm="HS256")
        return access_token
