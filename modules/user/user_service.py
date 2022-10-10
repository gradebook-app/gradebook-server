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
    
    def is_user_active(self, user:dict) -> bool: 
        logged_in_at = user.get("loggedInAt", None)
        if not logged_in_at: return False

    def get_user_account(self, genesisId): 
        return self.genesisService.account_details(genesisId)

    def get_schedule(self, genesisId, query): 
        response = self.genesisService.query_schedule(genesisId, query)
        return response