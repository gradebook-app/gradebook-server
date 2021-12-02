from modules.user.aggregations.user_aggregation import user_aggregation

class UserRepository: 
    def __init__(self, db): 
        self.db = db
        self.user_modal = self.db.get_collection("users")

    def update_one(self, filter, update): 
        response = self.user_modal.update_one(filter, update)
        return response

    def update_many(self, filter, update): 
        response = self.user_modal.update_many(filter, update)
        return response

    def query_aggregated_users(self, limit=15, skip=0): 
        return self.user_modal.aggregate(user_aggregation(limit, skip))