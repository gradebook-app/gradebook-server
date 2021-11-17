def user_aggregation(limit, skip):
    return [
        {
            "$match": { "status": "active" }
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
            "$limit": limit,
        },
        {
            "$skip": skip,
        }
    ]