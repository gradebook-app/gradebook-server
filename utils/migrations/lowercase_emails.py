from mongo_config import db

def lowercase_emails_migration():
    user_modal = db.get_collection("users")
    users = user_modal.find({ "email": { "$regex": "[A-Z]" }})
    for user in users: 
        user_modal.update_one({ "_id": user["_id"] }, { "$set": {
            "email": user["email"].lower()
        }})
        print("Updated Email: ", user["email"])


def delete_duplicate_emails_migration():
    user_modal = db.get_collection("users")
    users = user_modal.aggregate([
        {
            '$match': {
                'loggedInAt': {
                    '$ne': None
                }
            }
        }, {
            '$group': {
                '_id': {
                    '$toLower': '$email'
                }, 
                'emails': {
                    '$addToSet': {
                        'email': '$email', 
                        'createdAt': '$createdAt', 
                        'loggedInAt': '$loggedInAt', 
                        'userId': '$_id', 
                        'status': '$status'
                    }
                }
            }
        }, {
            '$project': {
                'size': {
                    '$size': '$emails'
                }, 
                'emails': {
                    '$sortArray': {
                        'input': '$emails', 
                        'sortBy': {
                            'loggedInAt': -1
                        }
                    }
                }
            }
        }, {
            '$sort': {
                'size': -1
            }
        }
    ])

    for user in users:
        if len(user["emails"]) <= 1: continue
        print(user["emails"][0]["loggedInAt"])

        for i in user["emails"][1:]: 
            print(i["loggedInAt"], i["userId"])
            deleted = user_modal.update_one({ "_id": i["userId"] },{ "$set": {
                "status": "deleted"
            }})
            print("Deleted: ", i["userId"])
        print()
