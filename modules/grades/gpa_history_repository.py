class GPAHistoryRepository:
    def __init__(self, db):
        self.db = db
        self.gpa_history_model = self.db.get_collection("gpa-history")

    def insert_one(self, doc):
        response = self.gpa_history_model.insert_one(doc)
        return response
