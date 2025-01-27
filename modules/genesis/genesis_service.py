import gc
import sys
import traceback
import requests
from requests.utils import quote as encodeURL
from pyquery import PyQuery as pq
import re
from constants.genesis import genesis_config
from modules.genesis.mt_service import MTService
from modules.user.types.user import GeneralUserAccount
from utils.grade import letter_to_number, number_to_letter
from utils.parser import parse
from urllib.parse import parse_qs
from flask import Response
import aiohttp
from http.cookies import SimpleCookie
from modules.genesis.sb_service import SBService
from fake_useragent import UserAgent

global_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

class GenesisService:
    def __init__(self):
        pass

    def get_global_headers(self):
        ua = UserAgent(browsers=["safari", "chrome"])
        return {**global_headers, "User-Agent": ua.random}

    async def fetch(self, session, method="GET", *args, **kwargs):
        if method == "GET":
            async with session.get(*args, **kwargs) as response:
                return response, await response.text()
        elif method == "POST":
            async with session.post(*args, **kwargs) as response:
                return response

    async def get_access_token(
        self, userId, password, school_district, specifiedStudentId, jsession_id
    ):
        genesis = genesis_config[school_district]
        email = f"{userId}"

        root_url = genesis["root"]
        auth_route = genesis["auth"]
        login_route = genesis["login"]

        landing_url = f"{root_url}{login_route}"
        auth_url = f"{root_url}{auth_route}"
        data = {"j_username": email, "j_password": password}
       
        headers = self.get_global_headers()
        if jsession_id:
            main_route = genesis["main"]
            # Validate Client Side retrieved JSESSIONID
            try:
                home_route = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary"
                login_res = requests.get(
                    home_route,
                    cookies={ "JSESSIONID": jsession_id},
                    headers=headers,
                )
 
                login_url_params = parse_qs(login_res.url.split("?")[1])
                studentId = login_url_params["studentid"][0]

                return [jsession_id, userId, True, specifiedStudentId or studentId]
            except Exception as e:
                if specifiedStudentId: 
                    return [jsession_id, userId, False, specifiedStudentId]

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            landing_response, _ = await self.fetch(
                session,
                method="GET",
                url=landing_url,
                headers=headers,
                allow_redirects=False,
            )

            genesisToken = None
            studentId = None

            cookie_str = landing_response.cookies
            cookie = SimpleCookie()
            cookie.load(cookie_str)

            cookies = {}
            for key, morsel in cookie.items():
                cookies[key] = morsel.value

            genesisToken = cookies.get("JSESSIONID", None)
            lastVisit = cookies.get("lastvisit", None)

            auth_response = await self.fetch(
                session,
                method="POST",
                url=auth_url,
                headers={
                    **headers,
                    "Cookie": f"JSESSIONID={genesisToken};lastvisit={lastVisit}",
                },
                data=data,
                allow_redirects=False,
            )

            access = False
            if "Location" in auth_response.headers and not auth_response.headers[
                "Location"
            ].__contains__(auth_route):
                access = True

            if access:
                try:
                    login_res = requests.get(
                        auth_response.headers["Location"],
                        cookies=cookies,
                        headers=headers,
                    )

                    login_url_params = parse_qs(login_res.url.split("?")[1])
                    studentId = login_url_params["studentid"][0]
                    del login_res
                except Exception as e:
                    {print("Error Getting Student ID", e)}

            del auth_response
            return [genesisToken, userId, access, specifiedStudentId or studentId]

    def access_granted(self, html):
        title = pq(html).find("title").text()
        if "login" in title.lower():
            return False
        else:
            return True

    def get_accounts(self, genesisId) -> GeneralUserAccount:
        genesis = genesis_config[genesisId["schoolDistrict"]]

        root_url = genesis["root"]
        main_route = genesis["main"]
        studentId = genesisId["studentId"]

        url = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary&studentid={studentId}&action=form"

        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())

        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )
        if not response.text:
            return {"accounts": []}

        html = response.text
        parser = pq(html)

        accounts = []

        raw_accounts = parser.find("#selectableStudents ul").children("li")
        for raw_account in raw_accounts:
            name_raw = pq(raw_account).find("a > div").children("div")[1]
            name = pq(name_raw).remove("div").text()
            student_id_raw = pq(raw_account).find("a").attr("onclick")
            student_id = re.findall("'.*'", student_id_raw)[0].replace("'", "")

            accounts.append(GeneralUserAccount(studentId=student_id, name=name))

        return {"accounts": accounts}

    def get_grades(self, query, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        markingPeriod = query["markingPeriod"]
        root_url = genesis["root"]
        main_route = genesis["main"]
        studentId = genesisId["studentId"]
        jession_id = query.get("token", genesisId["token"])

        url = f"{root_url}{main_route}?tab1=studentdata&tab2=gradebook&tab3=weeklysummary&action=form&studentid={studentId}&mpToView={markingPeriod}"
        cookies = {"JSESSIONID": jession_id}

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())

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
            all_classes = parser.find("div.itemContainer").children("div.twoColFlex")

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
                raw_grade = (
                    pq(school_class)
                    .find("div.gradebookGrid div:nth-child(1) span")
                    .text()
                )

                courseIdRaw = pq(school_class).attr("onclick")

                try:
                    courseIds = re.findall("'.*'", courseIdRaw)

                    [courseId, sectionId] = courseIds[0].replace("'", "").split(",")
                except Exception:
                    [courseId, sectionId] = ["", ""]

                try:
                    grade = (
                        int(raw_grade[:-1])
                        if genesisId["schoolDistrict"] == "sbstudents.org"
                        else float(raw_grade[:-1])
                    )
                except:
                    grade = None

                class_name = (
                    pq(school_class)
                    .find("div.twoColGridItem div:nth-child(1) span")
                    .text()
                )
                teacher = (
                    pq(school_class)
                    .find("div.twoColGridItem div:nth-child(2) div")
                    .text()
                    .strip()
                )

                grade_letter: str = (
                    pq(school_class)
                    .find("div.gradebookGrid div:nth-child(2) div")
                    .remove("div")
                    .text()
                )

                projected = False

                if grade_letter:
                    fg_text = "*PROJECTED"
                    if fg_text in grade_letter:
                        projected = True
                    grade_letter = grade_letter.replace(fg_text, "").strip()

                if not grade_letter and grade:
                    grade_letter = number_to_letter(grade)

                classes.append(
                    {
                        "teacher": teacher,
                        "grade": {
                            "percentage": grade,
                            "letter": grade_letter,
                            "projected": projected,  # Doesn't work for Montgomery
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
                session,
                method="GET",
                url=url,
                cookies=cookies,
                headers=self.get_global_headers(),
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
                comment: str = None
                try:
                    comment = pq(
                        pq(assignment)
                        .find("div[title='Teacher Comment']")
                        .children()[1]
                    ).text()

                    if not comment:
                        comment = (
                            pq(assignment).find(".customDialogContainer div").text()
                        )
                        comment = comment.replace('"', "").strip()
                except Exception:
                    pass

                columns = pq(assignment).children("td")
                date = pq(columns[0]).text().replace("\n", " ")

                course = pq(columns[1]).find("div:nth-child(1)").text()
                teacher = pq(columns[1]).find("div:nth-child(2)").text()

                category = pq(pq(columns[2]).children("div")[0]).text()
                name = pq(columns[2]).find("b").text()

                pq(assignment).remove("div[title='Teacher Comment']")
                grade_raw: str = pq(columns[3]).find("div").text()
                percentage = None

                if grade_raw:
                    grade_raw = grade_raw.removeprefix("Recently Updated")
                    try:
                        percentage = float(grade_raw[:-1])
                    except ValueError:
                        percentage = None

                points = pq(columns[3]).remove("div").text()

                data.append(
                    {
                        "markingPeriod": markingPeriod,
                        "date": date,
                        "comment": comment,
                        "course": course,
                        "teacher": teacher,
                        "category": category,
                        "name": name,
                        "message": None,
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

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())
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

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())
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

        name = pq(rows[1]).find("td:nth-child(2)").text()
        grade = pq(rows[1]).find("td:nth-child(3) > span:last-child").text()

        if genesisId["schoolDistrict"] == "sbstudents.org":
            lunch_balance = pq(rows[9]).find("td:nth-child(2)").text()
        else:
            lunch_balance = pq(rows[11]).find("td:nth-child(2)").text()

        if genesisId["schoolDistrict"] == "sbstudents.org":
            locker = parse(lambda: pq(rows[10]).find("td:nth-child(2)").text())
        else:
            locker = parse(lambda: pq(rows[12]).find("td:nth-child(2)").text())

        grade = parse(lambda: int(grade))

        return {
            "name": name,
            "grade": grade,
            "locker": locker,
            "studentId": studentId,
            "stateId": stateId,
            "school": school,
            "lunchBalance": lunch_balance,
        }

    def query_schedule(self, genesisId, query):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]
        date = query["date"]

        studentId = genesisId["studentId"]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=studentsummary&action=ajaxGetBellScheduleForDate&studentid={studentId}&scheduleDate={date}&schedView=daily"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())
        if not self.access_granted(response.text):
            return Response(
                "Session Expired",
                401,
            )

        html = pq(response.json())
        header = html.find("tr.listheading").text()
        courses = html.items('tr:not([class="listheading"])')
        classes = []

        if genesisId["schoolDistrict"] == "sbstudents.org":
            try:
                classes = SBService.get_highschool_schedule(courses)
            except:
                classes = MTService.get_schedule(courses)
        else:
            classes = MTService.get_schedule(courses)

        return {"courses": classes, "header": header}

    def query_past_grades(self, genesisId):
        genesis = genesis_config[genesisId["schoolDistrict"]]
        root_url = genesis["root"]
        main_route = genesis["main"]

        studentId = genesisId["studentId"]
        url = f"{root_url}{main_route}?tab1=studentdata&tab2=grading&tab3=history&action=form&studentid={studentId}"
        cookies = {"JSESSIONID": genesisId["token"]}

        response = requests.get(url, cookies=cookies, headers=self.get_global_headers())
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
                year = pq(columns[0]).find("div:nth-child(2)").text()
                gradeLevel = pq(columns[0]).find("div:nth-child(1)").text()

                if gradeLevel:
                    try:
                        gradeLevel = int(re.findall(r"\d+", gradeLevel)[0])
                    except ValueError or IndexError:
                        gradeLevel = None
                else:
                    gradeLevel = None

            if not gradeLevel is None:
                name = pq(columns[1]).find("div:nth-child(2)").text()
                gradeLetter = pq(columns[2]).text()

                pointsEarned = str(pq(columns[-1]).find("div:nth-child(2)"))
                br_index = pointsEarned.index("<br/>")
                pointsEarned = float(
                    pointsEarned[
                        br_index + 5 : br_index + pointsEarned[br_index:].index("</div")
                    ]
                )

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
                                else letter_to_number(gradeLetter),
                                "grade": percent if percent else gradeLetter,
                            },
                            "name": name,
                            "year": year,
                        }
                    )
                    weights[gradeLevel].append(
                        {
                            "weight": pointsEarned,
                            "name": name,
                        }
                    )

        return [past_grades, weights]
