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
                "let": {"userId": "$_id", "studentId": "$studentId"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": ["$userId", "$$userId"],
                                    },
                                    {"$eq": ["$studentId", "$$studentId"]},
                                ]
                            }
                        }
                    }
                ],
                "as": "assignments",
            }
        },
        {
            "$lookup": {
                "from": "grades",
                "let": {"userId": "$_id", "studentId": "$studentId"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": ["$userId", "$$userId"],
                                    },
                                    {"$eq": ["$studentId", "$$studentId"]},
                                ]
                            }
                        }
                    }
                ],
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
