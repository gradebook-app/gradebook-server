from flask import Response
from worker import conn
from mongo_config import connect_db
from modules.genesis.genesis_service import GenesisService
from modules.auth.auth_service import AuthService
import numpy as np
from utils.gpa_points import gpa_ap_points, gpa_honors_points, gpa_standard_points
from modules.firebase.fcm_service import FCMService
from bson import ObjectId, json_util
import time
import json
import asyncio
from modules.user.user_repository import UserRepository
from modules.grades.assignments_repository import AssignmentRepository 
from modules.grades.grades_repository import GradesRepository 
from modules.grades.gpa_history_repository import GPAHistoryRepository
from rq import Queue

low_queue = Queue('low', connection=conn)
default_queue = Queue('default', connection=conn)

class GradesService: 
    def __init__(self): 
        self.genesisService = GenesisService()

    def grades(self, query, genesisId): 
        response = self.genesisService.get_grades(query, genesisId)
        return response
    
    async def assignments(self, query, genesisId): 
        try: 
            response = await self.genesisService.get_assignments(query, genesisId)
        except Exception: response = []
        if isinstance(response, Response):
            return response

        return { "assignments": response }
    
    def save_gpa(self, user, unweighted=None, weighted=None, past=None): 
        user_repo = UserRepository(db=connect_db())

        user_repo.update_one({
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
        low_queue.enqueue(f=self.save_gpa, args=(user, unweighted, weighted, None))

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
        courses_raw = response[1]
        weights = response[2]

        if courses_raw and len(courses_raw) > 0: 
            courses = np.array(courses_raw).flatten()
        else: 
            return {}
        
        course_tallied = {}

        single_mp = len(courses_raw) == len(courses)

        if not single_mp: 
            for course in courses: 
                sectionId = course['sectionId']
                courseId = course['courseId']
                key = f'{courseId}-{sectionId}'
                try: course_tallied[key].append(course)
                except KeyError: course_tallied[key] = [ course ]

            course_averages = []

            for course_mps in course_tallied.values(): 
                course_grade_total = 0
                course_count = 0

                for course in course_mps: 
                    try: 
                        percentage = float(course['grade']['percentage'])
                        if percentage and percentage > 0: 
                            course_grade_total += percentage
                            course_count += 1
                    except Exception: continue
                
                average = course_grade_total / course_count if course_count > 0 else 0
                course_mps[0]['grade']['percentage'] = average
                course_averages.append(course_mps[0])

        gpa_unweighted_total = gpa_weighted_total = excluded_courses = course_points = 0
        course_loop = courses if single_mp else course_averages

        for course in course_loop: 
            percentage = course['grade']['percentage']
            percentage = round(float(percentage)) if percentage else percentage

            if percentage and percentage != 0: 
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
        
        divisor = course_points if course_points > 0 else (len(course_loop) - excluded_courses)
        final_gpa_weighted = gpa_weighted_total / divisor
        final_gpa_unweighted = gpa_unweighted_total / divisor

        return {
            "unweightedGPA": final_gpa_unweighted,
            "weightedGPA": final_gpa_weighted
        }

    def cleanup_classes(self, user, grades): 
        grade_repo = GradesRepository(db=connect_db())
        mp = grades['currentMarkingPeriod']
        courses = grades['courses']

        courses_stored = grade_repo.find_one({
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
                grade_repo.delete_one({ 
                    "userId": user["_id"],
                    "markingPeriod": mp,
                    "sectionId": course_stored["sectionId"],
                    "courseId": course_stored["courseId"],
                })

    def send_assignment_update(self, token, assignment): 
        fcm_service = FCMService()

        title = f"{assignment['course']} \nAssignment Update"
        message = f"Scored {int(assignment['grade']['percentage'])}% on {assignment['name']}"

        fcm_service.send_message(token=token, message=message, title=title)

    def send_grade_update(self, user, course, previous_percent, current_percent): 
        fcm_service = FCMService()
        notificationToken = user['notificationToken']

        if not notificationToken or previous_percent is None: return

        equality = "increased" if current_percent > previous_percent else "decreased"
        name = course["name"]
        message = f"Grade for {name} {equality} from {previous_percent}% to {current_percent}%"

        fcm_service.send_message(token=notificationToken, message=message, title=name)
        
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
        
        try: fcm_service.send_message(token=notificationToken, message=message, title=f'GPA Update')
        except Exception: pass

        gpa_repo = GPAHistoryRepository(db=connect_db())
        gpa_repo.insert_one({
            "userId": ObjectId(user["_id"]),
            "unweightedGPA": user["unweightedGPA"],
            "weightedGPA": user["weightedGPA"],
            "timestamp": time.time()
        })

        user_repo = UserRepository(db=connect_db())
        user_repo.update_one({
            "_id": ObjectId(user["_id"]),
        }, {
            "$set": {
                "unweightedGPA": gpa["unweightedGPA"],
                "weightedGPA": gpa["weightedGPA"],
            }
        })

    def save_grades(self, user, grades):
        grade_repo = GradesRepository(db=connect_db())
        mp = grades['currentMarkingPeriod']

        courses = grades['courses']
        
        for course in courses: 
            change = grade_repo.find_one_and_update(
                userId=user["_id"], mp=mp, course=course)
        
            try: 
                if not change == None: 
                    previous_percent = current_percent = None 

                    try: previous_percent = float(change["grade"]["percentage"])
                    except TypeError and ValueError: pass
                    try: current_percent = float(course["grade"]["percentage"])
                    except TypeError and ValueError: pass

                    assert not current_percent is None and not previous_percent is None

                    if not previous_percent == current_percent: 
                        default_queue.enqueue(f=self.send_grade_update, args=(user, course, previous_percent, current_percent))
            except AssertionError: pass

        self.cleanup_classes(user, grades)
    
    async def authenticate_user(self, user): 
        email = user['email']
        school_district = user['schoolDistrict']
        password = user['pass']

        auth_service = AuthService()
        genesis_service = GenesisService()
        
        dycrypted_password = auth_service.dyscrypt_password(password).decode()
  
        [ genesisToken, email, access, studentId ] = await genesis_service.get_access_token(email, dycrypted_password, school_district)

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

    def query_and_save_grades(self, genesisId, user):
        response = self.query_user_grade(genesisId)

        if response is None: 
            return

        all_mp_grades = response[0]
        
        for mp_grades in all_mp_grades:
            self.save_grades(user, mp_grades)

        gpa = self.caculate_gpa(response)
        unweighted = user["unweightedGPA"]

        if not gpa["unweightedGPA"] == unweighted and not unweighted is None: 
            default_queue.enqueue(f=self.send_gpa_update, args=(user, gpa))

    def save_persist_time(self, persist_time):
        user_repository = UserRepository(db=connect_db())

        try: 
            user_repository.update_many(
                { "status": "active" }, 
                { "$set": {
                    "lastPersistTimestamp": persist_time,
                }}
            )
        except Exception: pass
        finally: 
            pass
            # scheduler.enqueue_in(time_delta=timedelta(minutes=5), func=self.query_grades, skip=0)

    def clean_assignments(self, userId, assignments): 
        assignment_repository = AssignmentRepository(db=connect_db())

        ids = []

        for i in assignments: 
            ids.append(ObjectId(i['_id']))

        assignment_repository.delete_many({
            "userId": userId,
            "_id": { "$in": ids },
        })
    
    def store_assignments(self, user, assignments, send_notifications):
        assignment_repository = AssignmentRepository(db=connect_db())
        
        docs = []

        for i in assignments: 
            docs.append({
                "userId": user['_id'],
                "name": i['name'],
                "course": i['course'],
                "markingPeriod": i['markingPeriod'],
                "category": i['category'],
                "date": i['date'],
                "grade": {
                    "percentage": i['grade']['percentage'],
                    "points": i['grade']['points'],
                },
            })

        try: 
            assignment_repository.insert_many(docs)

            token = user['notificationToken']
            if not token or token is None or not send_notifications: return 
            for assignment_notificatinon in docs[:3]:
                default_queue.enqueue_call(func=self.send_assignment_update, args=(token, assignment_notificatinon))
        except Exception: 
            pass

    def find_assignments(self, all_assignments, assignments):
        docs = []

        for i in all_assignments:
            for j in assignments: 
                if i['name'] == json_util.loads(j)['name']: 
                    docs.append(i)
                
        return docs

    async def persist_assignments(self, user, persist_time):
        assignments = user['assignments']
        genesis_service = GenesisService()

        genesisId = await self.authenticate_user(user)
        
        if genesisId is None: 
            return 
        
        query = { "markingPeriod": "allMP", "courseId": "", "sectionId": "", "status": "GRADED" }
        response = await genesis_service.get_assignments(query, genesisId)
        
        serialized_new_assignments = []
        serialized_stored_assignments = []
    
        for i in response: 
            serialized_new_assignments.append(json.dumps({
                "name": i['name'],
                "course": i['course'],
                "markingPeriod": i['markingPeriod'],
                "category": i['category'],
                "date": i['date'],
                "percentage": i['grade']['percentage'],
                "points": i['grade']['points'],
                "userId": json_util.dumps(user["_id"])
            }))

        for i in assignments: 
            serialized_stored_assignments.append(json.dumps({
                "name": i['name'],
                "course": i['course'],
                "markingPeriod": i['markingPeriod'],
                "category": i['category'],
                "date": i['date'],
                "percentage": i['grade']['percentage'],
                "points": i['grade']['points'],
                "userId": json_util.dumps(i["userId"])
            }))

        try: 
            last_persist_timestamp = user['lastPersistTimestamp']
        except KeyError:
            last_persist_timestamp = 0 

        elapsed_time = int(persist_time - last_persist_timestamp)
        send_notification = elapsed_time < (60 * 60 * 6)

        if len(assignments): 
            new_assignments = set(serialized_new_assignments) - set(serialized_stored_assignments)
            removed_assignments = set(serialized_stored_assignments) - set(serialized_new_assignments)
            if len(new_assignments):
                new_assignments = self.find_assignments(response, list(new_assignments))
                default_queue.enqueue_call(func=self.store_assignments, args=(user, new_assignments, send_notification))
                default_queue.enqueue_call(func=self.query_and_save_grades, args=(genesisId, user))
            elif not len(new_assignments) and not len(user['grades']):
                default_queue.enqueue_call(func=self.query_and_save_grades, args=(genesisId, user))

            if len(removed_assignments): 
                removed_assignments = self.find_assignments(assignments, list(removed_assignments))
                default_queue.enqueue_call(func=self.clean_assignments, args=(user['_id'], removed_assignments, ))
        else: 
            send_notification = False
            default_queue.enqueue_call(func=self.store_assignments, args=(user, response, send_notification))
        if not len(assignments) and not len(user['grades']):
            default_queue.enqueue_call(func=self.query_and_save_grades, args=(genesisId, user))

    def query_grades(self, skip): 
        user_repository = UserRepository(db=connect_db())
        returned_total = None

        try: 
            persist_time = time.time()

            limit = 15 # find optimal number of users to query at once
        
            response = user_repository.query_aggregated_users(limit=limit, skip=skip)
            next_skip = skip + limit

            docs = list(response)
            returned_total = len(docs)
    
            startTime = time.time()
            loop = asyncio.get_event_loop()
            coros = [ self.persist_assignments(doc, persist_time) for doc in list(docs) ]
            loop.run_until_complete(asyncio.gather(*coros))
            loop.close()

            endTime = time.time()
            print(
                f"{skip}-{limit + skip if limit >= len(docs) else skip + len(docs)}: ", 
                endTime - startTime
            )
        except Exception: pass
        finally: 
            if returned_total == 0 or returned_total is None: 
                default_queue.enqueue_call(func=self.save_persist_time, args=(persist_time, ))
                next_skip = 0

            if next_skip != 0: 
                default_queue.enqueue_call(func=self.query_grades, args=(next_skip,))
