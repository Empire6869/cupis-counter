from selenium.webdriver.common.by import By
from time import sleep
import seleniumwire.undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import requests
from datetime import datetime, timedelta
import math
from loguru import logger

solver = TwoCaptcha("29952bd5475b49e0cbfbd26d05607ebb") 
proxyArray = [
    'https://user170118:nu0cgs@46.38.128.96:6984',
    'https://user170118:nu0cgs@212.16.80.140:6984',
    'https://user170118:nu0cgs@212.16.80.149:6984',
    'https://user170118:nu0cgs@212.16.80.125:6984',
    'https://user170118:nu0cgs@46.38.128.162:6984',
    'https://user170118:nu0cgs@212.16.80.70:6984',
    'https://user170118:nu0cgs@46.38.128.187:6984'
    ]
currentProxy = 0

class Reports:
    def __init__(self):
        global currentProxy
        # options = uc.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument(
        #     '--no-first-run --no-service-autorun --password-store=basic --enable-javascript')
        # options.headless = True
        ## Chrome Options
        chrome_options = uc.ChromeOptions()
        chrome_options.headless = True
        chrome_options.accept_insecure_certs=True
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic --enable-javascript')
        proxy_options = {}
        
        if (len(proxyArray)):
            proxyUrl = proxyArray[currentProxy]
            logger.info("Using proxy {url}, current proxy id {id}", url=proxyUrl, id=currentProxy)
            currentProxy = (currentProxy + 1) % len(proxyArray)
            proxy_options["proxy"] = {
                'http': proxyUrl,
                'https': proxyUrl,
                'no_proxy': 'localhost,127.0.0.1'
            }

        ## Create Chrome Driver
        self.driver = uc.Chrome(
            options=chrome_options,
            seleniumwire_options=proxy_options
        )
        sleep(2)

    def auth(self, username, password):
        try:
            self.driver.get('https://wallet.1cupis.ru/auth')

            timeout = 5
            element_present = EC.presence_of_element_located(
                (By.NAME, 'phone'))
            WebDriverWait(self.driver, timeout).until(element_present)
            self.driver.find_element(By.NAME, "phone").send_keys(username)
            self.driver.find_element(By.NAME, "password").send_keys(password)

            for i in range(10):
                try:
                    img = self.driver.find_element(By.XPATH,
                                                   '//div[@class="w-240px h-64px relative"]/img')
                    src = img.get_attribute('src')
                    res = solver.normal(src)
                    logger.debug("Solving captcha attempt {attempt}", attempt=i)
                    captchaEl = self.driver.find_element(
                        By.XPATH, '//input[@data-qa="captcha-input"]')
                    for i in range(6):
                        captchaEl.send_keys(Keys.BACK_SPACE)
                    captchaEl.send_keys(res["code"])
                    self.driver.find_element(
                        By.XPATH, '//button[@type="submit"]').click()

                    try:
                        element_present = EC.presence_of_element_located(
                            (By.XPATH, '//div[@class="bg-red-00 text-red-03 text-center p-8"]/p'))
                        WebDriverWait(self.driver, 5).until(element_present)
                        error = self.driver.find_element(
                            By.XPATH, '//div[@class="bg-red-00 text-red-03 text-center p-8"]/p').text
                        
                        logger.debug("Error auth {err}", err=error)

                        if error == 'Вы указали неправильный номер или пароль.':
                            return 'LoginPasswordError', False
                        
                        if error == 'Подозрительная активность. Попробуйте повторить позднее или обратитесь в службу поддержки.':
                            return 'SuspisiosActivity', False

                        if not error:
                            return None, True
                    except Exception as e:
                        try:
                            element_present = EC.presence_of_element_located(
                            (By.XPATH, '//div[@class="text-xs text-red-03"]'))
                            WebDriverWait(self.driver, 5).until(element_present)
                            error = self.driver.find_element(
                                By.XPATH, '//div[@class="text-xs text-red-03"]').text
                            
                            logger.debug("Error auth {err}", err=error)
                            
                            if error == 'В пароле должно быть как минимум 8 символов':
                                return 'PasswordTooShort', False
                            
                            if not error:
                                return None, True
                        except Exception as e:
                            return None, True
                        
                        return None, True
                except Exception as e:
                    print("E")
                    print(e)

            return 'MaxCaptchaAttempts', False
        except Exception as e:
            logger.error("Auth tech error {err}", err=e)
            return 'TechError', False

    def get_report(self, username, password):
        authSuccessTotal = False
        for i in range(3):
            [error, authSuccess] = self.auth(username, password)
            logger.info("Authentication status for {user} is {success}, error {err}", user=username, success=authSuccess, err=error)
            if authSuccess:
                authSuccessTotal = True
                break

            if error == 'LoginPasswordError':
                self.driver.close()
                return 'LoginPasswordError', None
            
            if error == 'PasswordTooShort':
                self.driver.close()
                return 'PasswordTooShort', None

        result = {
            "recordsCount": 0,
            "itemsAllTime": [],
            "itemsLastThreeMonths": [],
            "accountStatus": 'basic'
        }
        if not authSuccessTotal:
            self.driver.close()
            return 'TechAuthError', None
        
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
            logger.warning("Not able to get customer profile {user}, error {err}", user=username, err=e)

        bkAllTimeTotal = {}
        bkAllTimeDeposits = {}
        bkAllTimeWithdraws = {}
        bkLastThreeMonthTotal = {}
        bkLastThreeMonthsDeposits = {}
        bkLastThreeMonthsWithdraws = {}
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
                        if payment["title"] in bkAllTimeWithdraws:
                            bkAllTimeWithdraws[payment["title"]] += amount
                        else:
                            bkAllTimeWithdraws[payment["title"]] = amount
                    else:
                        if payment["title"] in bkAllTimeDeposits:
                            bkAllTimeDeposits[payment["title"]] += amount
                        else:
                            bkAllTimeDeposits[payment["title"]] = amount

                    if payment["title"] in bkAllTimeTotal:
                        bkAllTimeTotal[payment["title"]] += amount
                    else:
                        bkAllTimeTotal[payment["title"]] = amount

                    lastThreeMonths = datetime.strptime(payment["createdAt"], '%Y-%m-%dT%H:%M:%S.%f%z') + timedelta(days=30*3)
                    if lastThreeMonths.timestamp() > datetime.now().timestamp():
                        if payment["subtitle"] == "Выплата выигрыша":
                            if payment["title"] in bkLastThreeMonthsWithdraws:
                                bkLastThreeMonthsWithdraws[payment["title"]] += amount
                            else:
                                bkLastThreeMonthsWithdraws[payment["title"]] = amount
                        else:
                            if payment["title"] in bkLastThreeMonthsDeposits:
                                bkLastThreeMonthsDeposits[payment["title"]] += amount
                            else:
                                bkLastThreeMonthsDeposits[payment["title"]] = amount

                        if payment["title"] in bkLastThreeMonthTotal:
                            bkLastThreeMonthTotal[payment["title"]] += amount
                        else:
                            bkLastThreeMonthTotal[payment["title"]] = amount

        for [bkName, bkTotal] in bkAllTimeTotal.items():
            deposits = 0
            withdraws = 0
            if bkName in bkAllTimeDeposits:
                deposits = math.floor(bkAllTimeDeposits[bkName])

            if bkName in bkAllTimeWithdraws:
                withdraws = math.floor(bkAllTimeWithdraws[bkName])

            result["itemsAllTime"].append({"bkName": bkName, "total": math.floor(bkTotal), "deposits": deposits, "withdraws": withdraws})
        
        for [bkName, bkTotal] in bkLastThreeMonthTotal.items():
            deposits = 0
            withdraws = 0

            if bkName in bkLastThreeMonthsDeposits:
                deposits = math.floor(bkLastThreeMonthsDeposits[bkName])

            if bkName in bkLastThreeMonthsWithdraws:
                withdraws = math.floor(bkLastThreeMonthsWithdraws[bkName])

            result["itemsLastThreeMonths"].append({"bkName": bkName, "total": math.floor(bkTotal), "deposits": deposits, "withdraws": withdraws})

        result["recordsCount"] = recordsCount

        logger.info("Success fetching user report {user}, records count {count}", user=username, count=result["recordsCount"])
        self.driver.close()

        return None, result
