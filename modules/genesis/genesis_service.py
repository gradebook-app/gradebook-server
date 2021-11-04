import requests
from pyquery import PyQuery as pq
import re
from constants.genesis import genesis_config
from utils.grade import grade

class GenesisService: 
    def __init__(self): 
        pass

    def get_access_token(self, userId, password, school_district): 
        genesis = genesis_config[school_district]

        # email_suffix = genesis['email_suffix']
        email = f'{userId}'

        root_url = genesis['root']
        auth_route = genesis['auth']
        url = f'{root_url}{auth_route}'

        data = {'j_username': email, 'j_password': password }
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        response = requests.post(url, data=data, headers=headers, allow_redirects=False)

        access = False
        if not response.headers['Location'].endswith(auth_route):
            access = True

        cookies = dict(response.cookies)
        genesisToken = cookies['JSESSIONID']
        return [ genesisToken, userId, access ]
    
    def get_grades(self, query, genesisId): 
        genesis = genesis_config[genesisId['schoolDistrict']]
        markingPeriod = query['markingPeriod']

        root_url = genesis["root"]
        main_route = genesis["main"]
        studentId = genesisId['email'].split("@")[0]
     
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=gradebook&tab3=weeklysummary&action=form&studentid={studentId}&mpToView={markingPeriod}"
        cookies = { 'JSESSIONID': genesisId['token'] }
        response = requests.get(url, cookies=cookies)

        html = response.text
        parser = pq(html)
        classes = parser.find('table.list')
        all_classes = list(classes.items('tr[class="listrowodd"]')) + list(classes.items('tr[class="listroweven"]'))

        marking_period_options = parser.find("select[name='fldMarkingPeriod']").children("option")

        marking_periods = []
        current_marking_period = ""

        for i in marking_period_options: 
            optionTag = pq(i)
            value = optionTag.attr("value")
            if optionTag.attr('selected') == 'selected':
                current_marking_period = value
            marking_periods.append(value)

        classes = []

        for school_class in all_classes: 
            teacher = pq(school_class.children('td')[1]).remove('b').text()
            
            final_grade = str()
            final_grade_raw = pq(school_class.children('td')[2]).find("table tr > td").text()
            if not "no grades" in final_grade_raw.lower(): 
                final_grade = final_grade_raw.split("%")[0]

            raw_grade = school_class.find("td[title='View Course Summary'] > div").text()
            courseIdRaw = school_class.find("td.cellLeft > span.categorytab").attr("onclick")
            try: 
                courseIds = re.findall("'.*'", courseIdRaw)
                [ courseId, sectionId ] = courseIds[0].split(',')[1].replace("'", "").split(":")
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
                    "projected": bool(final_grade),
                },
                "name": class_name,
                "courseId": courseId,
                "sectionId": sectionId
            })

        response = {
            "courses": classes, 
            "markingPeriods": marking_periods,
            "currentMarkingPeriod": current_marking_period,
        }
        return response
    
    def get_assignments(self, query, genesisId): 
        genesis = genesis_config[genesisId['schoolDistrict']]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId['email'].split("@")[0]
        markingPeriod = "allMP" if query['markingPeriod'] == "FG" else query['markingPeriod'] 
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=gradebook&tab3=listassignments&studentid={studentId}&action=form&dateRange={markingPeriod}&courseAndSection={query['courseId']}:{query['sectionId']}&status="
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
            comment = pq(columns[6]).text()
            comment = comment.replace('"', '') if comment else ""

            data.append({
                "markingPeriod": marking_period,
                "date": date,
                "comment": comment,
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
    
    def course_weights(self, genesisId): 
        genesis = genesis_config[genesisId['schoolDistrict']]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId['email'].split("@")[0]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=grading&tab3=current&action=form&studentid={studentId}"
        cookies = { 'JSESSIONID': genesisId['token'] }

        response = requests.get(url, cookies=cookies)
        html = pq(response.text)
        table = html.find('table.list')
        rows = table.children('tr:not([class="listheading"])')

        courses = []

        for row in rows: 
            columns = pq(row).children('td')
            name = pq(columns[0]).text()
            teacher = pq(columns[3]).text()

            weight = pq(columns[-2]).text()
            weight = float(weight.strip()) if weight else None

            courses.append({
                "name": name,
                "teacher": teacher,
                "weight": weight,
            })
        
        return courses

    def account_details(self, genesisId): 
        genesis = genesis_config[genesisId['schoolDistrict']]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId['email'].split("@")[0]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary&action=form&studentid={studentId}"
        cookies = { 'JSESSIONID': genesisId['token'] }

        response = requests.get(url, cookies=cookies)
        html = pq(response.text)

        rows = html.find("td:nth-child(1) > table.list:nth-child(1)").children("tr")
        lunchBalance = pq(rows[6]).find("td:nth-child(2)").text()
        locker = pq(rows[7]).find("td:nth-child(2)").text()

        rows = html.find("td:nth-child(2) > table.list:nth-child(1)").children("tr")
        name = pq(rows[0]).find("td:nth-child(1)").text()
        
        grade = pq(pq(rows[0]).find("td:nth-child(2)").children("span")[1]).text()
        studentId = pq(rows[1]).find("td > span:nth-child(1)").text()
        stateId = pq(rows[1]).find("td > span:nth-child(2)").text()
        school = pq(rows[1]).find("td").remove("span").html().split("|")[0].strip()

        try: 
            grade = int(grade)
        except Exception: 
            grade= None

        return {
            "name": name,
            "grade": grade,
            "studentId": studentId,
            "stateId": stateId,
            "school": school,
            "lunchBalance": lunchBalance,
            "locker": locker,
        }

    def query_past_grades(self, genesisId): 
        genesis = genesis_config[genesisId['schoolDistrict']]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId['email'].split("@")[0]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=grading&tab3=history&action=form&studentid={studentId}"
        cookies = { 'JSESSIONID': genesisId['token'] }

        response = requests.get(url, cookies=cookies)
        html = pq(response.text)

        table = html.find('table.list')
        rows = table.children('tr:not([class="listheading"])')

        past_grades = {}
        weights = {}

        for row in rows: 
            columns = pq(row).children("td")
            gradeLevel = None

            if len(columns) > 1: 
                year = pq(columns[0]).text()
                gradeLevel = pq(columns[1]).text()

                if (gradeLevel):
                    try:
                        gradeLevel = int(gradeLevel)
                    except ValueError: 
                        gradeLevel = None
                else: gradeLevel = None

            if not gradeLevel is None: 
                name = pq(columns[2]).text()
                gradeLetter = pq(columns[4]).text()
                pointsEarned = pq(columns[-1]).text()
                
                if gradeLevel and gradeLevel >= 9:
                    if not past_grades.keys().__contains__(gradeLevel): 
                        past_grades[gradeLevel] = []
                        weights[gradeLevel] = []

                    past_grades[gradeLevel].append({
                        "grade": {
                            "percentage": grade(gradeLetter),
                            "grade": gradeLetter,
                        },
                        "name": name,
                        "year": year,
                    })
                    weights[gradeLevel].append({
                        "weight": float(pointsEarned),
                        "name": name,
                    })
        
        return [ past_grades, weights ]