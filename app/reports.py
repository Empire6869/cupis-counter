from selenium.webdriver.common.by import By
from time import sleep
import undetected_chromedriver as uc
import re
from twocaptcha import TwoCaptcha

solver = TwoCaptcha("29952bd5475b49e0cbfbd26d05607ebb")


class Reports:
    def __init__(self):
        option = uc.ChromeOptions()
        option.add_argument(
            '--no-first-run --no-service-autorun --password-store=basic')
        self.driver = uc.Chrome(options=option)

    def auth(self, username, password):
        self.driver.get('https://wallet.1cupis.ru/auth')
        sleep(3)
        self.driver.find_element(By.NAME, "phone").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)

        # TODO: Сделать капчу
        img = self.driver.find_element(By.XPATH,
                                       '//div[@class="w-240px h-64px relative"]/img')
        src = img.get_attribute('src')

        try:
            res = solver.normal(src)
            print(res)
            self.driver.find_element(
                By.XPATH, '//input[@data-qa="captcha-input"]').send_keys(res["code"])
            sleep(3)
            self.driver.find_element(
                By.XPATH, '//button[@type="submit"]').click()
        except Exception as e:
            print(e)

    def get_report(self, username, password):
        self.auth(username, password)
        sleep(10)
        # self.driver.get('https://wallet.1cupis.ru/history')
        # self.driver.find_element(
        #     By.XPATH, '//button[@type="button"]').click()
        # self.driver.close()


Reports().get_report('9126918544', 'Suleimanov1996A!')
