from requests_toolbelt.utils import dump
import requests
from pyquery import PyQuery as pq

class GenesisService: 
    def __init__(self): 
        pass

    def get_access_token(self, userId, password): 
        email = f'{userId}@sbstudents.org'
        url = 'https://parents.sbschools.org/genesis/sis/j_security_check'
        data = {'j_username': email, 'j_password': password }
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        response = requests.post(url, data=data, headers=headers, allow_redirects=False)
        cookies = dict(response.cookies)
        accessToken = cookies['JSESSIONID']
        return [ accessToken, userId ]
    
    def get_grades(accessToken): 
        url = "https://parents.sbschools.org/genesis/parents?tab1=studentdata&tab2=gradebook&tab3=weeklysummary&action=form&studentid=10024503"
        cookies = { 'JSESSIONID': accessToken }
        response = requests.get(url, cookies=cookies)

        html = response.text
        parser = pq(html)
        classes = parser.find('table.list')
        all_classes = list(classes.items('tr[class="listrowodd"]')) + list(classes.items('tr[class="listroweven"]'))
        for school_class in all_classes: 
            raw_grade = school_class.find("td[title='View Course Summary'] > div").text()
            grade = int(raw_grade[:-1])
            class_name = school_class.find("span.categorytab > font > u").text()
            print(class_name, grade)
        return classes.html()