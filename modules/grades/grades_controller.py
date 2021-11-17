from flask import Blueprint
from modules.grades.grades_service import GradesService
from utils.request_tools import query, genesisId
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
    response = loop.run_until_complete(grades_service.assignments(query, genesisId))
    loop.close()
    return response

@grades.route("/grades/gpa", methods=["GET"])
@genesisId
def getGPA(genesisId): 
    return grades_service.query_live_gpa(genesisId)

@grades.route("/grades/pastGPA", methods=["GET"])
@genesisId
def getPastGPA(genesisId): 
    return grades_service.query_past_grades(genesisId)