from pyquery import PyQuery as pq

class MTService: 
    @staticmethod
    def get_schedule(courses) -> list: 
        classes = []

        for course in courses:
            sections = pq(course).children("td")

            period = pq(sections[0]).find("b").text()   
            start_time, end_time = pq(sections[0]).remove("b").text().split("\n")
            
            name = pq(sections[1]).find("b").text()   
            class_data = pq(sections[1]).remove("b").text().split("\n")

            try: 
                teacher = class_data[0]
            except: 
                teacher = ""

            try: 
                room = class_data[1].replace("Room:", "")
            except: 
                room = ""

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