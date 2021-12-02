from pymongo.collection import ReturnDocument

class GradesRepository: 
    def __init__(self, db): 
        self.db = db
        self.grades_model = self.db.get_collection("grades")

    def find_one(self, filter): 
        response = self.grades_model.find(filter)
        return response

    def delete_one(self, filter): 
        response = self.grades_model.delete_one(filter)
        return response

    def find_one_and_update(self, userId, mp, course): 
        response = self.grades_model.find_one_and_update({
            "userId": userId,
            "markingPeriod": mp,
            "courseId": course["courseId"],
            "sectionId": course["sectionId"],
        }, {
            "$set": {
                "name": course["name"],
                "grade": {
                    "percentage": course["grade"]["percentage"],
                },
                "teacher": course["teacher"]
            }
        }, upsert=True, return_document=ReturnDocument.BEFORE)
        return response