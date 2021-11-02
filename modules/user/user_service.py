from mongo_config import db
from bson import ObjectId

class UserService: 
    def __init__(self): 
        pass

    def set_notification_token(self, token, genesisId):
        userId = genesisId["userId"]
        user_modal = db.get_collection("users")
        user_modal.find_one_and_update(
            { "_id": ObjectId(userId) },
            { "$set": { 
                "notificationToken": token,
            }}
        )
        
