import gspread
import locale
import os.path
import pytz
import schedule
import shutil
import time

from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sys import platform
from webdriver_manager.chrome import ChromeDriverManager

from my_settings import *

BASE_URL = 'https://my.mollie.com/dashboard/login?lang=en'
PAGE_URLS = ['https://my.mollie.com/dashboard/org_3743224/payments?status=paid%2Cpaidout',
             # 'https://my.mollie.com/dashboard/org_8385791/payments?status=paid%2Cpaidout',
             # 'https://my.mollie.com/dashboard/org_8843661/payments?status=paid%2Cpaidout',
             # 'https://my.mollie.com/dashboard/org_9081691/payments?status=paid%2Cpaidout',
             # 'https://my.mollie.com/dashboard/org_11931807/payments?status=paid%2Cpaidout',
             # 'https://my.mollie.com/dashboard/org_12418658/payments?status=paid%2Cpaidout',
             'https://my.mollie.com/dashboard/org_15375179/payments?status=paid%2Cpaidout',
             'https://my.mollie.com/dashboard/org_15673248/payments?status=paid%2Cpaidout',
             'https://my.mollie.com/dashboard/org_15725058/payments?status=paid%2Cpaidout']

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

locale.setlocale(locale.LC_TIME, "German")

creds = ServiceAccountCredentials.from_json_keyfile_name('client_key.json', scope)
client = gspread.authorize(creds)
sheets = client.open('New Payment API').worksheets()


def get_rows(driver):
    rows = []

    if len(driver.find_elements(By.XPATH, '//div[contains(@class, "grid-table__data")]/dl')) == 0:
        return rows

    today = datetime.now().astimezone()
    yesterday = today - timedelta(1)

    scrollHeight = driver.execute_script("return document.body.scrollHeight")
    scrollPos = 0
    for i in range(4):
        if scrollPos == scrollHeight:
            break
        scrollPos = scrollHeight
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        scrollHeight = driver.execute_script("return document.body.scrollHeight")

    ele_rows = driver.find_elements(By.XPATH, '//div[contains(@class, "grid-table__data")]/dl')
    for ele_row in ele_rows:
        id = ele_row.find_element(By.XPATH, './a').get_attribute('href').split('/')[-1]
        amount = ele_row.find_element(By.XPATH, './div[contains(@class, "cell-amount")]').text.replace(' €', '').replace('.', '').replace(',', '.')
        status = 'paid'
        ele_details = ele_row.find_element(By.XPATH, './div[contains(@class, "cell-details")]/div')
        details = driver.execute_script('return arguments[0].firstChild.textContent;', ele_details)
        createdAt = ele_row.find_element(By.XPATH, './div[contains(@class, "cell-date")]').text.replace(' um', '').replace(' Uhr', '')

        if createdAt.find('Heute') == 0:
            hours = createdAt[6:].split(':')
            createdAt = today.replace(hour=int(hours[0]), minute=int(hours[1])).astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:00+00:00')

        elif createdAt.find('Gestern') == 0:
            hours = createdAt[8:].split(':')
            createdAt = yesterday.replace(hour=int(hours[0]), minute=int(hours[1])).astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:00+00:00')

        else:
            days = createdAt.split()
            if days[1].find('.') > 0:
                days[1] = days[1][:3]
                createdAt = ' '.join(days)
                createdAt = datetime.strptime(createdAt, '%d. %b %y, %H:%M').astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:00+00:00')
            else:
                createdAt = datetime.strptime(createdAt, '%d. %B %y, %H:%M').astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:00+00:00')

        rows.append([id, createdAt, amount, details, status])

    return rows


def start():
    try:
        chrome_options = Options()
        chrome_options.add_argument("window-size=1200,1000")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
        chrome_options.add_argument(f'Upgrade-Insecure-Requests=1')
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument('--verbose')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')

        if platform == "win32" or platform == "win64":
            data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'selenium')
            chrome_options.add_argument(f"--user-data-dir={data_dir}")
            # chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        startedAt = datetime.now().timestamp()
        print("Start! : " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

        time.sleep(3)
        driver.get(BASE_URL)
        time.sleep(3)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="email"]')))
            ele_email = driver.find_element(By.XPATH, '//input[@id="email"]')
            ele_email.click()
            ele_email.clear()
            ele_email.send_keys(USERNAME)
            time.sleep(3)
            ele_password = driver.find_element(By.XPATH, '//input[@id="password"]')
            ele_password.click()
            ele_password.clear()
            ele_password.send_keys(PASSWORD)
            time.sleep(1)
            ele_password.send_keys(Keys.ENTER)
            time.sleep(7)
        except:
            pass

        if len(driver.find_elements(By.XPATH, '//div[@id="root"]')) == 1:

            for index in range(len(PAGE_URLS)):
                driver.get(PAGE_URLS[index])
                time.sleep(7)

                if driver.current_url != PAGE_URLS[index]:
                    continue

                rows = get_rows(driver)

                if index == 0:
                    with open('mollie.csv', 'w', encoding='utf-8') as of:
                        of.writelines(','.join(row) + '\n' for row in rows)
                else:
                    with open('mollie.csv', 'a+', encoding='utf-8') as of:
                        of.writelines(','.join(row) + '\n' for row in rows)

                records = sheets[index].get_all_records()

                last_row_index = 1
                record_ids = []
                for record in records:
                    if not record['id']:
                        break
                    last_row_index += 1
                    record_ids.append(record['id'])

                for row in reversed(rows):
                    if row[0] not in record_ids:
                        last_row_index += 1
                        sheets[index].update(f'A{last_row_index}:F{last_row_index}', [row])

        driver.close()
        driver.quit()

        print("End! : " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

        if datetime.now().timestamp() - startedAt < 60:
            shutil.rmtree('selenium')
    except:
        pass


if __name__ == "__main__":
    if platform == "linux" or platform == "linux2":
        display = Display(visible=0, size=(1200, 1000))
        display.start()

    schedule.every(1).hour.do(start)
    start()

    while True:
        schedule.run_pending()
        time.sleep(60)
