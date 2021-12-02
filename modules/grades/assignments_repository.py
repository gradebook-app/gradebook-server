class AssignmentRepository: 
    def __init__(self, db): 
        self.db = db
        self.assignment_model = self.db.get_collection("assignments")

    def delete_many(self, filter): 
        response = self.assignment_model.delete_many(filter)
        return response

    def insert_many(self, docs): 
        response = self.assignment_model.insert_many(docs)
        return response
