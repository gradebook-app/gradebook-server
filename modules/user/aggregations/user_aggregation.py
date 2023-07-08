def user_aggregation(limit, skip):
    return [
        {
            "$match": {
                "status": "active",
                "notificationToken": {"$ne": None},
                "studentId": {"$ne": None},
            }
        },
        {
            "$lookup": {
                "from": "assignments",
                "localField": "_id",
                "foreignField": "userId",
                "as": "assignments",
            }
        },
        {
            "$lookup": {
                "from": "grades",
                "localField": "_id",
                "foreignField": "userId",
                "as": "grades",
            }
        },
        {
            "$skip": skip,
        },
        {
            "$limit": limit,
        },
    ]
