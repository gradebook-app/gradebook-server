from flask import Blueprint
from modules.grades.grades_service import GradesService
from utils.request_tools import body, query, genesisId
import asyncio

grades = Blueprint('grades', __name__)
grades_service = GradesService()

@grades.route('/grades', methods=['GET'])
@query
@genesisId
def getGrades(query, genesisId): 
    return grades_service.grades(query, genesisId)

@grades.route('/grades/assignments', methods=["GET"])
@query
@genesisId
def getAssignments(query, genesisId): 
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    [ response ] = loop.run_until_complete(
        asyncio.gather(
            grades_service.assignments(query, genesisId),
        )
    )

    loop.close()
    return response

@grades.route('/grades/weight', methods=["GET"])
@query
@genesisId
def getCourseWeight(query, genesisId):
    weight = grades_service.course_weight(query['courseId'], query['sectionId'], genesisId)  
    return weight    

@grades.route('/grades/weight', methods=['POST'])
@body
@genesisId
def setCourseWeight(body, genesisId): 
    weight = dict(body).get('weight')
    courseId = body['courseId'] 
    sectionId = body['sectionId']
    response = grades_service.set_course_weight(courseId, sectionId, weight, genesisId)
    success = dict(response).get('weight', None) == weight if response else False
    return { 
        "success":  success, 
        "weight": weight if response else None
    }

@grades.route("/grades/gpa", methods=["GET"])
@genesisId
def getGPA(genesisId): 
    return grades_service.query_live_gpa(genesisId)

@grades.route("/grades/pastGPA", methods=["GET"])
@genesisId
def getPastGPA(genesisId): 
    return grades_service.query_past_grades(genesisId)

@grades.route("/grades/widgetGrades")
@body
def getWidgetGrades(_body): 
    return { "grades": "93%" }