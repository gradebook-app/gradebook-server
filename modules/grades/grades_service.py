from pymongo.collection import ReturnDocument
from rq import Queue
from worker import conn
from mongo_config import db
from modules.genesis.genesis_service import GenesisService
from modules.auth.auth_service import AuthService

q = Queue(connection=conn)

class GradesService: 
    def __init__(self): 
        self.genesisService = GenesisService()

    def grades(self, query, genesisId): 
        response = self.genesisService.get_grades(query, genesisId)
        return response
    
    def assignments(self, query, genesisId): 
        response = self.genesisService.get_assignments(query, genesisId)
        return { "assignments": response }

    def cleanup_classes(self, user, grades): 
        grade_modal = db.get_collection("grades")
        mp = grades['currentMarkingPeriod']
        courses = grades['courses']

        courses_stored = grade_modal.find({
            "userId": user["_id"],
            "markingPeriod": mp,
        })

        for course_stored in courses_stored:
            course_exist = False 
            for course in courses: 
                if course["sectionId"] == course_stored["sectionId"] and course["courseId"] == course_stored["courseId"]:
                    course_exist = True
            if not course_exist: 
                # legacy course deleted
                grade_modal.delete_one({ 
                    "userId": user["_id"],
                    "markingPeriod": mp,
                    "sectionId": course_stored["sectionId"],
                    "courseId": course_stored["courseId"],
                })

    def save_grades(self, user, grades):
        grade_modal = db.get_collection("grades")
        mp = grades['currentMarkingPeriod']

        courses = grades['courses']
        
        for course in courses: 
            change = grade_modal.find_one_and_update({
                "userId": user["_id"],
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
        
            if not change == None: 
                previous_percent = change["grade"]["percentage"]
                current_percent = course["grade"]["percentage"] 
                if not previous_percent == current_percent: 
                    print("Grade Change") # send notification 

        self.cleanup_classes(user, grades)
    

    def query_user_grade(self, user): 
        email = user['email']
        school_district = user['schoolDistrict']
        password = user['pass']

        auth_service = AuthService()
        genesis_service = GenesisService()
        
        dycrypted_password = auth_service.dyscrypt_password(password).decode()
        [ genesisToken, email, access ] = genesis_service.get_access_token(email, dycrypted_password, school_district)
        
        if not access: return

        query = { "markingPeriod": "" }
        genesisId = { 
            "schoolDistrict": school_district, 
            "token": genesisToken,
            "email": email,
        }

        grades = genesis_service.get_grades(query, genesisId)
        mps = grades['markingPeriods']

        for mp in mps:   
            if mp.lower().strip() == "fg": return
            mp_query = { "markingPeriod": mp }
            mp_grades = genesis_service.get_grades(mp_query, genesisId)
            self.save_grades(user, mp_grades)

    def query_grades(self, skip): 
        limit = 100
        user_modal = db.get_collection("users")
        response = user_modal.find({ "status": "active" }).limit(limit).skip(skip)
        next_skip = skip + limit

        docs = list(response)
        returned_total = len(docs)

        for doc in list(docs): 
            q.enqueue_call(func=self.query_user_grade, args=(doc,))

        if returned_total == 0: 
            next_skip = 0

        if next_skip != 0: 
            q.enqueue_call(func=self.query_grades, args=(next_skip,))
