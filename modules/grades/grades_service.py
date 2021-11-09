from pymongo.collection import ReturnDocument
from flask import Response
from rq import Queue
from worker import conn
from mongo_config import db
from modules.genesis.genesis_service import GenesisService
from modules.auth.auth_service import AuthService
import numpy as np
from utils.gpa_points import gpa_ap_points, gpa_honors_points, gpa_standard_points
from modules.firebase.fcm_service import FCMService
from bson import ObjectId
import time
from rq_scheduler import Scheduler

q = Queue(connection=conn)
scheduler = Scheduler(queue=q, connection=conn)

class GradesService: 
    def __init__(self): 
        self.genesisService = GenesisService()

    def grades(self, query, genesisId): 
        response = self.genesisService.get_grades(query, genesisId)
        return response
    
    def assignments(self, query, genesisId): 
        response = self.genesisService.get_assignments(query, genesisId)
        if isinstance(response, Response):
            return response

        return { "assignments": response }
    
    def save_gpa(self, user, unweighted=None, weighted=None, past=None): 
        user_modal = db.get_collection("users")

        user_modal.update({
            "_id": ObjectId(user["_id"])
        }, {
            "$set": {
                "unweightedGPA": unweighted,
                "weightedGPA": weighted,
                "pastGPA": past
            }
        })

    def query_live_gpa(self, genesisId): 
        response = self.query_user_grade(genesisId)

        if isinstance(response, Response):
            return response

        gpa = self.caculate_gpa(response)

        user = { "_id": genesisId["userId"] }
        unweighted = gpa["unweightedGPA"]
        weighted = gpa["weightedGPA"]
        q.enqueue(f=self.save_gpa, args=(user, unweighted, weighted, None))

        return gpa

    def query_past_grades(self, genesisId):
        response = self.genesisService.query_past_grades(genesisId)
        if isinstance(response, Response):
            return response


        courses = response[0]
        weights = response[1]
        gpas = []

        for key in courses.keys(): 
            gradeCourses = courses[key]
            gradeWeights = weights[key]
            calculated_gpa = self.caculate_gpa([ None, gradeCourses, gradeWeights ])
            gpas.append({
                **calculated_gpa, "gradeLevel": key, "year": courses[key][0]["year"],
            })

        return { "pastGradePointAverages": gpas }

    def caculate_gpa(self, response): 
        courses = response[1]
        weights = response[2]

        if courses and len(courses) > 0: 
            courses = np.array(courses).flatten()
        else: 
            return {}
        
        gpa_unweighted_total = 0
        gpa_weighted_total = 0
        excluded_courses = 0
        course_points = 0

        for course in courses: 
            percentage = course['grade']['percentage']
            percentage = float(percentage) if percentage else percentage

            if (percentage and percentage != 0): 
                name = course["name"]

                for weight in weights: 
                    if weight['name'] == name: 
                        course_points += weight['weight'] if weight['weight'] else 0
                        course_weight = weight['weight'] if weight['weight'] else 1

                points = gpa_standard_points(percentage)
                gpa_unweighted_total += (points * course_weight) 

                if name.lower().split().__contains__('honor') or name.lower().split().__contains__('honors'):
                    weighted_point = gpa_honors_points(percentage)
                elif name.lower().split().__contains__('ap'):
                    weighted_point = gpa_ap_points(percentage)
                else: 
                    weighted_point = gpa_standard_points(percentage)
                gpa_weighted_total += (weighted_point * course_weight)

            else:
                excluded_courses += 1

        divisor = course_points if course_points > 0 else (len(courses) - excluded_courses)
        final_gpa_weighted = gpa_weighted_total / divisor
        final_gpa_unweighted = gpa_unweighted_total / divisor

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

    def send_grade_update(self, user, course, previous_percent, current_percent): 
        fcm_service = FCMService()
        notificationToken = user['notificationToken']

        if not notificationToken: return

        equality = "increased" if current_percent > previous_percent else "decreased"
        name = course["name"]
        message = f"Grade for {name} {equality} from {previous_percent}% to {current_percent}%"

        fcm_service.send_message(token=notificationToken, message=message, title=f'Grade {equality.capitalize()}')
        
    def send_gpa_update(self, user, gpa): 
        fcm_service = FCMService()
        notificationToken = user['notificationToken']

        round_gpa = lambda x: round(x * (10 ** 4)) / (10 ** 4)

        unweighted_user = round_gpa(user["unweightedGPA"])
        weighted_user = round_gpa(user["weightedGPA"])

        current_unweighted = round_gpa(gpa["unweightedGPA"])
        current_weighted = round_gpa(gpa["weightedGPA"])

        if not notificationToken: return

        message = f"Unweighted GPA went from {unweighted_user} to {current_unweighted} and weighted GPA went from {weighted_user} to {current_weighted}."
        fcm_service.send_message(token=notificationToken, message=message, title=f'GPA Change')

        gpa_modal = db.get_collection("gpa-history")
        gpa_modal.insert_one({
            "userId": ObjectId(user["_id"]),
            "unweightedGPA": user["unweightedGPA"],
            "weightedGPA": user["weightedGPA"],
            "timestamp": time.time()
        })

        user_modal = db.get_collection("users")
        user_modal.update_one({
            "_id": ObjectId(user["_id"]),
        }, {
            "$set": {
                "unweightedGPA": gpa["unweightedGPA"],
                "weightedGPA": gpa["weightedGPA"],
            }
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
                    q.enqueue(f=self.send_grade_update, args=(user, course, previous_percent, current_percent))

        self.cleanup_classes(user, grades)
    
    def authenticate_user(self, user): 
        email = user['email']
        school_district = user['schoolDistrict']
        password = user['pass']

        auth_service = AuthService()
        genesis_service = GenesisService()
        
        dycrypted_password = auth_service.dyscrypt_password(password).decode()
  
        [ genesisToken, email, access, studentId ] = genesis_service.get_access_token(email, dycrypted_password, school_district)

        if not access: return None
    
        genesisId = { 
            "schoolDistrict": school_district, 
            "token": genesisToken,
            "email": email,
            "studentId": studentId,
        }

        return genesisId


    def query_user_grade(self, genesisId): 
        genesis_service = GenesisService()

        query = { "markingPeriod": "" }
        
        grades = genesis_service.get_grades(query, genesisId)

        if isinstance(grades, Response):
            return grades

        mps = grades['markingPeriods']
        current_mp = grades['currentMarkingPeriod']
        mps.remove(current_mp)
  
        all_mp_grades = []
        all_mp_coures = []

        all_mp_grades.append(grades)
        all_mp_coures.append(grades['courses'])
        
        course_weights = genesis_service.course_weights(genesisId)

        for mp in mps:   
            if not mp.lower().strip() == "fg": 
                mp_query = { "markingPeriod": mp }
                mp_grades = genesis_service.get_grades(mp_query, genesisId)
                all_mp_grades.append(mp_grades)
                all_mp_coures.append(mp_grades["courses"])
        
        return ( all_mp_grades, all_mp_coures, course_weights )

    def query_and_save_grades(self, user):
        genesisId = self.authenticate_user(user)
        response = self.query_user_grade(genesisId)
  
        if response is None: 
            return

        gpa = self.caculate_gpa(response)
        unweighted = user["unweightedGPA"]

        if not gpa["unweightedGPA"] == unweighted and not unweighted is None: 
            q.enqueue(f=self.send_gpa_update, args=(user, gpa))
        
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

