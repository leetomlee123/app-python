import hashlib

import redis
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# 获取redis数据库连接
r = redis.StrictRedis(host="121.37.139.13", port=6379, db=1, password='zx222lx')

def getResorce(url):
    try:

        chrome_opt = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2,
                 'excludeSwitches': ['enable-automation']
                 }
        chrome_opt.add_experimental_option("prefs", prefs)
        chrome_opt.add_argument('--headless')
        chrome_opt.add_argument('--disable-gpu')
        path = Service(r'/root/chromedriver')
        chrome_opt.add_argument("--no-sandbox")
        chrome_opt.add_argument("window-size=1024,768")
        chrome_opt.add_argument('--disable-dev-shm-usage')
        chrome_opt.add_argument("--remote-debugging-port=9222")
        browser = webdriver.Chrome(options=chrome_opt, executable_path=r'/root/chromedriver')
        browser.get(url=url)
        element = browser.find_element(by=By.XPATH, value='//audio[@id="jp_audio_0"]')
        return element.get_attribute('src')

    except Exception as e:
        print(e)


if __name__ == '__main__':
    url = 'https://www.ting13.com/play/421_1_85438.html'

    # print(getResorce(url))

    hexdigest = hashlib.md5(url.encode('utf-8')).hexdigest()


    print(hexdigest)
