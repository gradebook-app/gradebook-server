from pymongo.collection import ReturnDocument
from bson import ObjectId
from pymongo.database import Database


class GradesRepository:
    def __init__(self, db: Database):
        self.db = db
        self.grades_model = self.db.get_collection("grades")

    def find_one(self, filter):
        response = self.grades_model.find(filter)
        return response

    def find_course_weight(self, courseId, sectionId, userId: ObjectId, studentId):
        response = self.grades_model.find_one(
            {
                "courseId": courseId,
                "sectionId": sectionId,
                "userId": userId,
                "studentId": studentId
            }
        )
        return response

    def find_courses_if_weight(self, userId: ObjectId):
        response = self.grades_model.find({"userId": userId, "weight": {"$ne": None}})
        return response

    def update_course_weight(self, courseId, sectionId, weight, userId: ObjectId, studentId=None):
        response = self.grades_model.find_one_and_update(
            {"userId": userId, "sectionId": sectionId, "courseId": courseId, "studentId": studentId},
            {"$set": {"weight": weight}},
            return_document=ReturnDocument.AFTER,
        )

        return response

    def delete_one(self, filter):
        response = self.grades_model.delete_one(filter)
        return response

    def find_one_and_update(self, userId, mp, course, studentId=None):
        response = self.grades_model.find_one_and_update(
            {
                "userId": userId,
                "markingPeriod": mp,
                "courseId": course["courseId"],
                "sectionId": course["sectionId"],
                "studentId": studentId
            },
            {
                "$set": {
                    "name": course["name"],
                    "grade": {
                        "percentage": course["grade"]["percentage"],
                    },
                    "teacher": course["teacher"],
                }
            },
            upsert=True,
            return_document=ReturnDocument.BEFORE,
        )
        return response
