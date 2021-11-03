from types import coroutine
from pymongo.collection import ReturnDocument
from rq import Queue
from worker import conn
from mongo_config import db
from modules.genesis.genesis_service import GenesisService
from modules.auth.auth_service import AuthService
import numpy as np
from utils.gpa_points import gpa_ap_points, gpa_honors_points, gpa_standard_points

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

    def caculate_gpa(self, genesisId): 
        response = self.query_user_grade(genesisId)
        courses = response[1]
        if courses and len(courses) > 0: 
            courses = np.array(courses).flatten()
        else: 
            return {}
        
        gpa_unweighted_total = 0
        gpa_weighted_total = 0
        excluded_courses = 0

        for course in courses: 
            percentage = course['grade']['percentage']
            if (percentage != 0): 
                points = gpa_standard_points(percentage)
                gpa_unweighted_total += points

                name = course["name"]
                if name.lower().split().__contains__('honor') or name.lower().split().__contains__('honors'):
                    weighted_point = gpa_honors_points(percentage)
                elif name.lower().split().__contains__('ap'):
                    weighted_point = gpa_ap_points(percentage)
                else: 
                    weighted_point = gpa_standard_points(percentage)
                gpa_weighted_total += weighted_point

            else:
                excluded_courses += 1

        final_gpa_weighted = gpa_weighted_total / (len(courses) - excluded_courses)
        final_gpa_unweighted = gpa_unweighted_total / (len(courses) - excluded_courses)

        return {
            "unweightedGPA": final_gpa_unweighted,
            "weightedGPA": final_gpa_weighted
        }

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
    
    def authenticate_user(self, user): 
        email = user['email']
        school_district = user['schoolDistrict']
        password = user['pass']

        auth_service = AuthService()
        genesis_service = GenesisService()
        
        dycrypted_password = auth_service.dyscrypt_password(password).decode()
  
        [ genesisToken, email, access ] = genesis_service.get_access_token(email, dycrypted_password, school_district)

        if not access: return None
    
        genesisId = { 
            "schoolDistrict": school_district, 
            "token": genesisToken,
            "email": email,
        }

        return genesisId


    def query_user_grade(self, genesisId): 
        genesis_service = GenesisService()

        query = { "markingPeriod": "" }
        
        grades = genesis_service.get_grades(query, genesisId)
        mps = grades['markingPeriods']
  
        all_mp_grades = []
        all_mp_coures = []

        for mp in mps:   
            if not mp.lower().strip() == "fg": 
                mp_query = { "markingPeriod": mp }
                mp_grades = genesis_service.get_grades(mp_query, genesisId)
                all_mp_grades.append(mp_grades)
                all_mp_coures.append(mp_grades["courses"])
        
        return ( all_mp_grades, all_mp_coures )

    def query_and_save_grades(self, user):
        genesisId = self.authenticate_user(user)
        response = self.query_user_grade(genesisId)
  
        if response is None: 
            return
        
        all_mp_grades = response[0]

        for mp_grades in all_mp_grades:
            self.save_grades(user, mp_grades)

    def query_grades(self, skip): 
        limit = 100
        user_modal = db.get_collection("users")
        response = user_modal.find({ "status": "active" }).limit(limit).skip(skip)
        next_skip = skip + limit

        docs = list(response)
        returned_total = len(docs)

        for doc in list(docs): 
            q.enqueue_call(func=self.query_and_save_grades, args=(doc,))

        if returned_total == 0: 
            next_skip = 0

        if next_skip != 0: 
            q.enqueue_call(func=self.query_grades, args=(next_skip,))
