from flask import Blueprint
from modules.grades.grades_service import GradesService
from utils.request_tools import query, genesisId

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
    return grades_service.assignments(query, genesisId)
