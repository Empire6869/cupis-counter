from selenium.webdriver.common.by import By
from time import sleep
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import requests
from datetime import datetime, timedelta
import math

solver = TwoCaptcha("29952bd5475b49e0cbfbd26d05607ebb")


class Reports:
    def __init__(self):
        option = uc.ChromeOptions()
        option.add_argument(
            '--no-first-run --no-service-autorun --password-store=basic --no-sandbox')
        self.driver = uc.Chrome(options=option, headless=True)

    def auth(self, username, password):
        try:
            self.driver.get('https://wallet.1cupis.ru/auth')
            sleep(5)

            timeout = 5
            element_present = EC.presence_of_element_located(
                (By.NAME, 'phone'))
            WebDriverWait(self.driver, timeout).until(element_present)
            self.driver.find_element(By.NAME, "phone").send_keys(username)
            self.driver.find_element(By.NAME, "password").send_keys(password)

            authSuccess = False
            for i in range(10):
                try:
                    img = self.driver.find_element(By.XPATH,
                                                   '//div[@class="w-240px h-64px relative"]/img')
                    src = img.get_attribute('src')
                    res = solver.normal(src)
                    print(f"Solving captcha {i} attempt")
                    captchaEl = self.driver.find_element(
                        By.XPATH, '//input[@data-qa="captcha-input"]')
                    for i in range(6):
                        captchaEl.send_keys(Keys.BACK_SPACE)
                    captchaEl.send_keys(res["code"])
                    self.driver.find_element(
                        By.XPATH, '//button[@type="submit"]').click()

                    try:
                        element_present = EC.presence_of_element_located(
                            (By.XPATH, '//div[@class="bg-red-00 text-red-03 text-center p-8"]'))
                        WebDriverWait(self.driver, 5).until(element_present)
                        error = self.driver.find_element(
                            By.XPATH, '//div[@class="bg-red-00 text-red-03 text-center p-8"]').text
                        print(error)

                        if not error:
                            return True
                    except Exception as e:
                        return True
                except Exception as e:
                    print(e)

            return authSuccess
        except Exception as e:
            print(e)
            return False

    def get_report(self, username, password):
        for i in range(3):
            authSuccess = self.auth(username, password)
            print("Auth success")
            print(authSuccess)
            print("I")
            print(i)
            if authSuccess:
                break

        result = {
            "recordsCount": 0,
            "itemsAllTime": [],
            "itemsLastThreeMonths": [],
            "accountStatus": 'basic'
        }
        if not authSuccess:
            return result
        
        self.driver.get('https://wallet.1cupis.ru/history')
        s = requests.Session()
        selenium_user_agent = self.driver.execute_script(
            "return navigator.userAgent;")
        s.headers.update({"user-agent": selenium_user_agent})
        for cookie in self.driver.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'],
                          domain=cookie['domain'])
            
        try:
            accountResponse = s.get('https://wallet.1cupis.ru/profile-api/v1/customer')
            accountReponseJson = accountResponse.json()
            result["accountStatus"] = accountReponseJson["responseData"]["identification"].lower()
        except Exception as e:
            print(e)

        bkAllTimeTotal = {}
        bkLastThreeMonthTotal = {}
        recordsCount = 0
        hasMore = True
        lastFetchedRecordsDateTime = None
        while hasMore:
            filterParams = {"filter": {"paymentTypes": [], "merchantIds": [], "hasCashback": False}, "size": 50}
            if lastFetchedRecordsDateTime:
                filterParams["filter"]["until"] = lastFetchedRecordsDateTime

            response = s.post(
                "https://wallet.1cupis.ru/profile-api/v2/payment/find", json=filterParams)
            jsonData = response.json()

            if len(jsonData["responseData"]["payments"]) < 50:
                hasMore = False
                
            for payment in jsonData["responseData"]["payments"]:
                lastFetchedRecordsDateTime = payment["createdAt"]

                if payment["paymentStatus"]["paymentStatusType"] == 'COMPLETED':
                    recordsCount += 1
                    amount = -abs(float(payment["amount"]["amount"]))
                    if payment["subtitle"] == "Выплата выигрыша":
                        amount = abs(amount)
                    if payment["title"] in bkAllTimeTotal:
                        bkAllTimeTotal[payment["title"]] += amount
                    else:
                        bkAllTimeTotal[payment["title"]] = amount

                    lastThreeMonths = datetime.strptime(payment["createdAt"], '%Y-%m-%dT%H:%M:%S.%f%z') + timedelta(days=30*3)
                    if lastThreeMonths.timestamp() > datetime.now().timestamp():
                        if payment["title"] in bkLastThreeMonthTotal:
                            bkLastThreeMonthTotal[payment["title"]] += amount
                        else:
                            bkLastThreeMonthTotal[payment["title"]] = amount

        for [bkName, bkTotal] in bkAllTimeTotal.items():
            result["itemsAllTime"].append({"bkName": bkName, "total": math.floor(bkTotal)})
        
        for [bkName, bkTotal] in bkLastThreeMonthTotal.items():
            result["itemsLastThreeMonths"].append({"bkName": bkName, "total": math.floor(bkTotal)})

        result["recordsCount"] = recordsCount

        print("result")
        print(result)
        self.driver.close()

        return result
