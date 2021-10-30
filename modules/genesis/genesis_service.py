import requests
from pyquery import PyQuery as pq
import re

class GenesisService: 
    def __init__(self): 
        pass

    def get_access_token(self, userId, password): 
        email = f'{userId}@sbstudents.org'
        url = 'https://parents.sbschools.org/genesis/sis/j_security_check'
        data = {'j_username': email, 'j_password': password }
        print(email, password)
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        response = requests.post(url, data=data, headers=headers, allow_redirects=False)

        access = False
        if response.headers['Location'].startswith("https://parents.sbschools.org:443/genesis/parents"):
            access = True

        cookies = dict(response.cookies)
        genesisToken = cookies['JSESSIONID']
        return [ genesisToken, userId, access ]
    
    def get_grades(self, query, genesisId): 
        url = f"https://parents.sbschools.org/genesis/parents?tab1=studentdata&tab2=gradebook&tab3=weeklysummary&action=form&studentid={genesisId['userId']}&mpToView=MP1"
        cookies = { 'JSESSIONID': genesisId['token'] }
        response = requests.get(url, cookies=cookies)

        html = response.text
        parser = pq(html)
        classes = parser.find('table.list')
        all_classes = list(classes.items('tr[class="listrowodd"]')) + list(classes.items('tr[class="listroweven"]'))

        classes = []

        for school_class in all_classes: 
            teacher = pq(school_class.children('td')[1]).remove('b').text()
            raw_grade = school_class.find("td[title='View Course Summary'] > div").text()
            courseIdRaw = school_class.find("td[title='View Course Summary']").attr("onclick")
        
            try: 
                courseIds = re.findall("'.*'", courseIdRaw)
                [ courseId, sectionId ] = courseIds[0].replace("'", "").split(",")
            except Exception: 
                [ courseId, sectionId ] = ["", ""]

            
            try: 
                grade = int(raw_grade[:-1])
            except: 
                grade = None

            class_name = school_class.find("span.categorytab > font > u").text()
            grade_letter = school_class.find("td[title='View Course Summary'] ~ td").text()
        
            classes.append({
                "teacher": teacher,
                "grade": {
                    "percentage": grade,
                    "letter": grade_letter,
                },
                "name": class_name,
                "courseId": courseId,
                "sectionId": sectionId
            })

        response = { "courses": classes }
        return response
    
    def get_assignments(self, query, genesisId): 
        studentId = genesisId['userId']
        url = f"https://parents.sbschools.org/genesis/parents?tab1=studentdata&tab2=gradebook&tab3=listassignments&studentid={studentId}&action=form&dateRange=allMP&courseAndSection={query['courseId']}:{query['sectionId']}&status="
        cookies = { 'JSESSIONID': genesisId['token'] }

        response = requests.get(url, cookies=cookies)
        html = response.text
        parser = pq(html)
        table = parser.find('table.list')
        assignments = table.children('tr:not([class="listheading"])')

        data = []

        for assignment in assignments: 
            columns = pq(assignment).children('td')
            marking_period = pq(columns[0]).text()
            date = pq(columns[1]).text()
            [ courseElement, teacherElement ] = pq(columns[2]).items("div")
            course = courseElement.text()
            teacher = teacherElement.text()
            category = pq(columns[3]).remove('div').text()
            name = pq(columns[4]).remove('div').text()

            gradeDivs = pq(columns[5]).children('div')
            percentage = None

            if gradeDivs.length: 
                try: 
                    percentage = int(pq(gradeDivs[-1]).remove('div').text()[:-1])
                except ValueError: 
                    percentage = None

            points = pq(columns[5]).remove('div').text()
            data.append({
                "markingPeriod": marking_period,
                "date": date,
                "course": course,
                "teacher": teacher,
                "category": category,
                "name": name,
                "grade": {
                    "points": points,
                    "percentage": percentage,
                }
            })
        return data