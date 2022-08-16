from mongo_config import db

def add_timestamps_migration(): 
    user_modal = db.get_collection("users")
    users = user_modal.find({ "createdAt": None })
    
    for user in users: 
       user_modal.update_one(
        { 
            "createdAt": None,
             "_id": user["_id"] 
        }, {
            "$set": {
                "createdAt": user.get("_id").generation_time
            }
        })