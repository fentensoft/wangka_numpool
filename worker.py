"""
Spider implements.

Created by Tony Liu (388848@163.com)
Date: 02/11/2018
"""
import requests
import json
import re
import time
import threading
from regex_tags import regexTags
from database import getDatabaseConnection


def getDistrictCode():
    r = requests.get("https://m.10010.com/king/kingNumCard/init?product=0&channel=67")
    parsed = json.loads(r.text)
    ret = []
    for province in parsed["provinceData"]:
        tmp = {"code": province["PROVINCE_CODE"], "province": province["PROVINCE_NAME"]}
        tmp["group"] = parsed["proGroupNum"][tmp["code"]]
        tmp["city"] = []
        for city in parsed["cityData"][tmp["code"]]:
            tmp["city"].append({"name": city["CITY_NAME"], "code": city["CITY_CODE"]})
        ret.append(tmp)
    return ret


class Matcher(object):

    def __init__(self, r):
        self.re = re.compile(r[0])
        self.tag = r[1]
    
    def match(self, s):
        if self.re.search(s):
            return self.tag
        return ""


class Worker(threading.Thread):

    def __init__(self, province, provinceCode, city, cityCode, groupKey):
        self.matchers = list(map(Matcher, regexTags))
        self.province = province
        self.provinceCode = provinceCode
        self.city = city
        self.cityCode = cityCode
        self.groupKey = groupKey
        self.rollingCount = []
        self.running = True
        self.autoTerminate = True
        self.history = []
        super(Worker, self).__init__()

    def getNum(self):
        conn = getDatabaseConnection()
        try:
            r = requests.get("https://m.10010.com/NumApp/NumberCenter/qryNum", params={
                "callback": "jsonp_queryMoreNums",
                "provinceCode": self.provinceCode,
                "cityCode": self.cityCode,
                "groupKey": self.groupKey,
                "searchCategory": "3",
                "net": "01",
                "qryType": "02",
                "goodsNet": "4"
            })
            nums = re.findall(r"\d{11}", r.text)
            ret = map(lambda num: (num, self.makeTag(num)), nums)
            cur = conn.cursor()
            cur.executemany("INSERT OR IGNORE INTO tbl_numbers(number, tag) VALUES(?, ?);", ret)
            conn.commit()
            if cur.rowcount > 0:
                self.history.append((time.strftime("%Y-%m-%d %H:%M:%S"), cur.rowcount))
                if len(self.history) == 201:
                    self.history.pop(0)
            return len(nums), cur.rowcount
        except:
            return 0, 0
        finally:
            conn.close()
    
    def makeTag(self, n):
        return "," + ",".join([i for i in map(lambda r: r.match(n), self.matchers) if i]) + ","
    
    def run(self):
        self.running = True
        while self.running:
            _, c = self.getNum()
            self.rollingCount.append(c)
            if len(self.rollingCount) == 101:
                self.rollingCount.pop(0)
                if (sum(self.rollingCount) < 10) and (self.autoTerminate):
                    break
            time.sleep(3)

    def stop(self):
        self.running = False
