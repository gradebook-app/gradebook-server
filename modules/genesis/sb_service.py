from pyquery import PyQuery as pq


# Specific HTML Parsing Functions for South Brunswick Genesis
class SBService:
    @staticmethod
    def get_lunch_balance(html):
        locker = pq(html[7]).find("td:nth-child(2)").text()
        return locker

    @staticmethod
    def get_locker_code(html):
        # locker = pq(html[7]).find("td:nth-child(2)").text()
        return None
