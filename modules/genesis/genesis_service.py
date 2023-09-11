import gc
import traceback
import requests
from requests.utils import quote as encodeURL
from pyquery import PyQuery as pq
import re
from constants.genesis import genesis_config
from utils.grade import grade
from urllib.parse import parse_qs
from flask import Response
import aiohttp
from http.cookies import SimpleCookie
from modules.genesis.sb_service import SBService

global_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
}


class GenesisService:
    def __init__(self):
        pass

    async def fetch(self, session, method="GET", *args, **kwargs):
        if method == "GET":
            async with session.get(*args, **kwargs) as response:
                return response, await response.text()
        elif method == "POST":
            async with session.post(*args, **kwargs) as response:
                return response

    async def get_access_token(self, userId, password, school_district):
        genesis = genesis_config[school_district]
        email = f"{userId}"

        root_url = genesis["root"]
        auth_route = genesis["auth"]

        auth_url = f"{root_url}{auth_route}?j_username={encodeURL(email)}&j_password={encodeURL(password)}"

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=64, verify_ssl=False)
        ) as session:
            auth_response = await self.fetch(
                session,
                method="POST",
                url=auth_url,
                headers=global_headers,
                allow_redirects=False,
            )
            access = False
            if not auth_response.headers["Location"].__contains__(auth_route):
                access = True

            genesisToken = None
            studentId = None

            cookie_str = auth_response.cookies
            cookie = SimpleCookie()
            cookie.load(cookie_str)

            cookies = {}
            for key, morsel in cookie.items():
                cookies[key] = morsel.value

            genesisToken = cookies["JSESSIONID"]

            if access:
                try:
                    login_res = requests.get(
                        auth_response.headers["Location"],
                        cookies=cookies,
                        headers=global_headers,
                    )
                    login_url_params = parse_qs(login_res.url.split("?")[1])
                    studentId = login_url_params["studentid"][0]
                    del login_res
                except Exception as e:
                    {print("Error Getting Student ID", e)}

            del auth_response
            return [genesisToken, userId, access, studentId]

    def access_granted(self, html):
        title = pq(html).find("title").text()
        if "login" in title.lower():
            return False
        else:
            return True

    def get_grades(self, query, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        markingPeriod = query["markingPeriod"]

        root_url = genesis["root"]
        main_route = genesis["main"]
        studentId = genesisId["studentId"]

        url = f"{root_url}{main_route}?tab1=studentdata&tab2=gradebook&tab3=weeklysummary&action=form&studentid={studentId}&mpToView={markingPeriod}"

        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=global_headers)

        if not response.text:
            return {
                "courses": None,
                "markingPeriods": None,
                "currentMarkingPeriod": None,
            }

        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        try:
            if not self.access_granted(response.text):
                return Response(
                    "Session Expired",
                    401,
                )

            html = response.text
            parser = pq(html)
            classes = parser.find("table.list")
            all_classes = list(classes.items('tr[class="listrowodd"]')) + list(
                classes.items('tr[class="listroweven"]')
            )

            marking_period_options = parser.find(
                "select[name='fldMarkingPeriod']"
            ).children("option")

            marking_periods = []
            current_marking_period = ""

            for i in marking_period_options:
                optionTag = pq(i)
                value = optionTag.attr("value")
                if optionTag.attr("selected") == "selected":
                    current_marking_period = value
                marking_periods.append(value)

            classes = []

            for school_class in all_classes:
                teacher = pq(school_class.children("td")[1]).remove("b").text()

                final_grade = str()
                final_grade_raw = (
                    pq(school_class.children("td")[2]).find("table tr > td").text()
                )
                if (
                    not "no grades" in final_grade_raw.lower()
                    and not "not graded" in final_grade_raw.lower()
                ):
                    final_grade = final_grade_raw.split("%")[0]

                raw_grade = school_class.find(
                    "td[title='View Course Summary'] > div"
                ).text()
                courseIdRaw = school_class.find("td.cellLeft > span.categorytab").attr(
                    "onclick"
                )

                try:
                    courseIds = re.findall("'.*'", courseIdRaw)
                    [courseId, sectionId] = (
                        courseIds[0].split(",")[1].replace("'", "").split(":")
                    )
                except Exception:
                    [courseId, sectionId] = ["", ""]

                try:
                    grade = int(raw_grade[:-1])
                except:
                    grade = None

                class_name = school_class.find("span.categorytab > font > u").text()
                grade_letter = school_class.find(
                    "td[title='View Course Summary'] ~ td"
                ).text()

                classes.append(
                    {
                        "teacher": teacher,
                        "grade": {
                            "percentage": grade if grade else final_grade,
                            "letter": grade_letter,
                            "projected": bool(
                                final_grade
                            ),  # Doesn't work for Montegomery
                        },
                        "name": class_name,
                        "courseId": courseId,
                        "sectionId": sectionId,
                    }
                )

            query_response = {
                "courses": classes,
                "markingPeriods": marking_periods,
                "currentMarkingPeriod": current_marking_period,
            }

            del response
            return query_response
        except Exception as e:
            print("Exception @ query grades", traceback.format_exception_only(e))
            gc.collect(generation=2)

            del response
            return {
                "courses": None,
                "markingPeriods": None,
                "currentMarkingPeriod": None,
            }

    async def get_assignments(self, query, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId["studentId"]

        markingPeriod = (
            "allMP" if query["markingPeriod"] == "FG" else query["markingPeriod"]
        )
        courseId = query["courseId"]
        sectionId = query["sectionId"]

        course_and_section = f"{courseId}:{sectionId}" if courseId and sectionId else ""

        try:
            status = query["status"] if "status" in dict(query).keys() else ""
        except KeyError:
            status = ""

        url = f"{root_url}{main_route}?tab1=studentdata&tab2=gradebook&tab3=listassignments&studentid={studentId}&action=form&dateRange={markingPeriod}&courseAndSection={course_and_section}&status={status}"
        cookies = {"JSESSIONID": genesisId["token"]}

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=64, verify_ssl=False)
        ) as session:
            _, text = await self.fetch(
                session, method="GET", url=url, cookies=cookies, headers=global_headers
            )

            if not self.access_granted(text):
                return Response(
                    "Session Expired",
                    401,
                )
            parser = pq(text)
            table = parser.find("table.list")
            assignments = table.children('tr:not([class="listheading"])')

            data = []

            for assignment in assignments:
                message = None
                columns = pq(assignment).children("td")
                marking_period = pq(columns[0]).text()
                date = pq(columns[1]).text()
                [courseElement, teacherElement] = pq(columns[2]).items("div")
                course = courseElement.text()
                teacher = teacherElement.text()
                category = pq(columns[3]).remove("div").text()
                name = pq(columns[4]).remove("div").text()

                try:
                    points_raw = columns[5]
                    _, points_text = (
                        pq(i).text() for i in pq(points_raw).find("div").children("div")
                    )
                    if points_text:
                        message = points_text
                except Exception:
                    pass

                gradeDivs = pq(columns[5]).children("div")
                percentage = None

                if gradeDivs.length:
                    try:
                        percentage = float(pq(gradeDivs[-1]).remove("div").text()[:-1])
                    except ValueError:
                        percentage = None

                points = pq(columns[5]).remove("div").text()

                comment = pq(columns[6]).text()
                comment = comment.replace('"', "") if comment else ""

                data.append(
                    {
                        "markingPeriod": marking_period,
                        "date": date,
                        "comment": comment,
                        "course": course,
                        "teacher": teacher,
                        "category": category,
                        "name": name,
                        "message": message,
                        "grade": {
                            "points": points,
                            "percentage": percentage,
                        },
                    }
                )
            return data

    def course_weights(self, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId["studentId"]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=grading&tab3=current&action=form&studentid={studentId}"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=global_headers)
        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        html = pq(response.text)
        table = html.find("table.list")
        rows = table.children('tr:not([class="listheading"])')

        courses = []

        for row in rows:
            try:
                columns = pq(row).children("td")
                name = pq(columns[0]).text()
                teacher = pq(columns[3]).text()

                weight = pq(columns[-2]).text()
                weight = float(weight.strip()) if weight else None

                courses.append(
                    {
                        "name": name,
                        "teacher": teacher,
                        "weight": weight,
                    }
                )
            except Exception:
                continue

        return courses

    def account_details(self, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId["studentId"]

        url = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary&action=form&studentid={studentId}"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=global_headers)
        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        html = pq(response.text)
        rows = html.find("td:nth-child(1) > table.list:nth-child(1)").children("tr")

        school = pq(rows[1]).text()
        studentId, stateId = pq(rows[2].find("td")).children()
        studentId = pq(studentId.find("span")).text()
        stateId = pq(stateId.find("span")).text()

        rows = pq(html.find("table.notecard")).find("table.list").children("tr")

        lunch_balance =  lunch_balance = pq(rows[9]).find("td:nth-child(2)").text()
     
        # try:
        #     if genesisId["schoolDistrict"] == "sbstudents.org":
        #         locker = SBService.get_locker_code(rows)
        #     else:
        #         locker = pq(rows[7]).find("td:nth-child(2)").text()
        # except Exception:
        #     locker = None

        # rows = html.find("td:nth-child(2) > table.list:nth-child(1)").children("tr")
        # name = pq(rows[0]).find("td:nth-child(1)").text()

        # grade = pq(pq(rows[0]).find("td:nth-child(2)").children("span")[1]).text()

        # try:
        #     grade = int(grade)
        # except Exception:
        #     grade = None

        return {
            "studentId": studentId,
            "stateId": stateId,
            "school": school,
            "lunchBalance": lunch_balance
        }
        # return {
        #     "name": name,
        #     "grade": grade,
        #     "lunchBalance": lunchBalance,
        #     "locker": locker,
        # }

    def query_schedule(self, genesisId, query):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]
        date = query["date"]

        studentId = genesisId["studentId"]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary&action=ajaxGetBellScheduleForDate&studentid={studentId}&scheduleDate={date}&schedView=daily"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=global_headers)
        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        html = pq(response.json())
        header = html.find("tr.listheading").text()
        courses = html.items('tr:not([class="listheading"])')
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

        return {"courses": classes, "header": header}

    def query_past_grades(self, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId["studentId"]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=grading&tab3=history&action=form&studentid={studentId}"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=global_headers)
        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        html = pq(response.text)

        table = html.find("table.list")
        rows = table.children('tr:not([class="listheading"])')

        past_grades = {}
        weights = {}

        for row in rows:
            columns = pq(row).children("td")
            gradeLevel = None

            if len(columns) > 1:
                year = pq(columns[0]).text()
                gradeLevel = pq(columns[1]).text()

                if gradeLevel:
                    try:
                        gradeLevel = int(gradeLevel)
                    except ValueError:
                        gradeLevel = None
                else:
                    gradeLevel = None

            if not gradeLevel is None:
                name = pq(columns[2]).text()
                gradeLetter = pq(columns[4]).text()
                pointsEarned = pq(columns[-1]).text()

                try:
                    percent = float(gradeLetter)
                except ValueError:
                    percent = None

                if gradeLevel and gradeLevel >= 9:
                    if not past_grades.keys().__contains__(gradeLevel):
                        past_grades[gradeLevel] = []
                        weights[gradeLevel] = []

                    past_grades[gradeLevel].append(
                        {
                            "grade": {
                                "percentage": percent
                                if percent
                                else grade(gradeLetter),
                                "grade": percent if percent else gradeLetter,
                            },
                            "name": name,
                            "year": year,
                        }
                    )
                    weights[gradeLevel].append(
                        {
                            "weight": float(pointsEarned),
                            "name": name,
                        }
                    )

        return [past_grades, weights]
