from mongo_config import db


# add student ids to each GPA history object
def add_student_ids_to_gpa_history_migration():
    user_modal = db.get_collection("users")
    gpa_history = db.get_collection("gpa-history")
    users = user_modal.find(
        {
            "studentId": {"$ne": None},
        }
    )

    for user in users:
        gpa_history.update_many(
            {"userId": user["_id"], "studentId": None},
            {"$set": {"studentId": user["studentId"]}},
        )
        print(f"Finished Migration for {user['_id']}")


# add student ids to each Grade object
def add_student_ids_to_grades_migration():
    user_modal = db.get_collection("users")
    grades = db.get_collection("grades")
    users = user_modal.find(
        {
            "studentId": {"$ne": None},
        }
    )

    for user in users:
        grades.update_many(
            {"userId": user["_id"], "studentId": None},
            {"$set": {"studentId": user["studentId"]}},
        )
        print(f"Finished Migration for {user['_id']}")


# add student ids to each Assignment object
def add_student_ids_to_assignments_migration():
    user_modal = db.get_collection("users")
    assignments = db.get_collection("assignments")
    users = user_modal.find(
        {
            "studentId": {"$ne": None},
        }
    )

    for user in users:
        assignments.update_many(
            {"userId": user["_id"], "studentId": None},
            {"$set": {"studentId": user["studentId"]}},
        )
        print(f"Finished Migration for {user['_id']}")
