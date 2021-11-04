from mongo_config import db
from bson import ObjectId
from modules.genesis.genesis_service import GenesisService

class UserService: 
    def __init__(self): 
        self.genesisService = GenesisService()

    def set_notification_token(self, token, genesisId):
        userId = genesisId["userId"]
        user_modal = db.get_collection("users")
        user_modal.find_one_and_update(
            { "_id": ObjectId(userId) },
            { "$set": { 
                "notificationToken": token,
            }}
        )
        return {}
    
    def get_user_account(self, genesisId): 
        return self.genesisService.account_details(genesisId)
