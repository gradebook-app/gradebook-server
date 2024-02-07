from flask import Blueprint
from modules.auth.auth_service import AuthService
from utils.request_tools import body, genesisId
import asyncio

auth = Blueprint("auth", __name__)
auth_service = AuthService()


@auth.route("/auth/login", methods=["POST"])
@body
def login(body):
    userId, password, school_district = (
        body["userId"],
        body["pass"],
        body["schoolDistrict"],
    )

    jsession_id = body.get("jSessionId", None)
    notificationToken = body.get("notificationToken", None)
    specifiedStudentId = body.get("studentId", None)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(
        auth_service.login(
            userId,
            password,
            school_district,
            notificationToken,
            specifiedStudentId,
            jsession_id,
        )
    )
    loop.close()
    return response


@auth.route("/auth/logout", methods=["POST"])
@body
def logout(body):
    return auth_service.logout(body)
