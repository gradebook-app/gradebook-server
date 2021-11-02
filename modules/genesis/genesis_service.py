import requests
from pyquery import PyQuery as pq
import re
from constants.genesis import genesis_config

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