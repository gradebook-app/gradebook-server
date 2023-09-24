# Specific HTML Parsing Functions for South Brunswick Genesis
class SBService:
    @staticmethod
    def get_highschool_schedule(courses) -> list: 
        classes = []

        for course in courses:
            sections = course.items("div")

            period = next(sections).text()
            start_time = next(sections).text()
            end_time = next(sections).text()
            name = next(sections).text()
            teacher = next(sections).text()
            room = next(sections).text()

            classes.append(
                {
                    "period": period,
                    "startTime": start_time,
                    "endTime": end_time,
                    "name": name,
                    "teacher": teacher,
                    "room": room,
                }
            )

        return classes
