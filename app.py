import hashlib
import logging
import os
from aligo import Aligo
import pymongo as pymongo
import requests
from flask import Flask, request, jsonify
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
executor = ThreadPoolExecutor()
import json
# 要执行的命令
command = "ps -ef|grep -v grep|grep chrome|awk '{print $2}'|xargs kill -9"
host='127.0.0.1'
# host = '121.37.139.13'
# 执行命令


# 执行命令

md5 = hashlib.md5()
app = Flask(__name__)
import redis
ali = Aligo()
# 获取redis数据库连接
pool = redis.ConnectionPool(host=host, port=6379, decode_responses=True, db=1, password='zx222lx')
r = redis.Redis(connection_pool=pool)
myclient = pymongo.MongoClient(
    'mongodb://lx:Lx123456@%s:27017/' % host, connect=False)
mydb = myclient["book"]
voiceDB = mydb["voice"]


def get_proxy():
    proxy_json = requests.get("http://%s:5010/get/?" % host).json()
    return proxy_json


def delete_proxy(proxy):
    print('delete proxy %s' % proxy)
    requests.get("http://%s:5010/delete/?proxy={}" % host.format(proxy))
def run(params):
    try:
        a = urlparse(params['bookSrc'])
        file_name = os.path.basename(a.path)
        _, file_suffix = os.path.splitext(file_name)

        # path = "d://%s_%s%s" % (params['bookName'], params['title'], file_suffix)
        path = "/usr/tmp/%s_%s%s" % (params['bookName'], params['title'], file_suffix)
        file = ali.get_file_by_path(path)
        if file:
            return
        r = requests.get(params['bookSrc'], stream=True)

        with open(r"%s" % path, "wb") as f:
            for chunk in r.iter_content(chunk_size=512):
                f.write(chunk)
        remote_folder = ali.get_folder_by_path('voice/%s' % params['bookName'])
        if not remote_folder:
            ali.create_folder(params['bookName'], ali.get_folder_by_path("voice").file_id)
            remote_folder = ali.get_folder_by_path('voice/%s' % params['bookName'])

        ali.upload_file(path, parent_file_id=remote_folder.file_id)
    except Exception as e:
        print(e)
    finally:
        os.remove(path)
def getResorce(url):
    try:
        output = os.system(command)

        chrome_opt =ChromeOption()
        prefs = {"profile.managed_default_content_settings.images": 2,
                 'excludeSwitches': ['enable-automation']
                 }
        chrome_opt.add_experimental_option("prefs", prefs)
        try:
            proxy = get_proxy()
            if proxy['https']:
                htp = 'https://' + proxy['proxy']
            else:
                htp = 'http://' + proxy['proxy']
            print(htp)
            chrome_opt.add_argument("--proxy-server=%s" % htp)
        except Exception as e:
            print(str(e))

        chrome_opt.add_argument('--headless')
        chrome_opt.add_argument('--disable-gpu')
        path = Service(r'/root/chromedriver')
        chrome_opt.add_argument("--no-sandbox")
        chrome_opt.add_argument('--incognito')  # 隐身模式（无痕模式）
        chrome_opt.add_argument("window-size=1024,768")
        chrome_opt.add_argument('--disable-dev-shm-usage')
        chrome_opt.add_argument("--remote-debugging-port=9222")
        browser = webdriver.Chrome(options=chrome_opt, executable_path=r'/root/chromedriver')
        browser.get(url=url)
        element = browser.find_element(by=By.XPATH, value='//audio[@id="jp_audio_0"]')
        content = browser.find_element(by=By.XPATH, value='//meta[@property="og:title"]').get_attribute('content')
        bookName = browser.find_element(by=By.XPATH, value='//meta[@name="_n"]').get_attribute('content')
        bookDesc = browser.find_element(by=By.XPATH, value='//meta[@name="_t"]').get_attribute('content')
        bookSrc = element.get_attribute('src')
        if bookSrc is None:
            delete_proxy(proxy)
            return bookSrc


        executor.submit(run,{
            "title": content,
            "bookName": bookName,
            "bookDesc": bookDesc,
            "bookSrc": bookSrc
        })

        return bookSrc

    except Exception as e:
        delete_proxy(proxy)
        print(e)


def retryGetResource(url):
    retry_count = 3
    while retry_count > 0:
        try:
            resorce = getResorce(url)
            return resorce
        except Exception:
            retry_count -= 1
    return None


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World'


@app.route('/url', methods=["POST"])
def hello_world1():  # put application's code here
    url = request.form.get("url")
    logging.info(url)
    print(url)

    md51 = hashlib.md5(url.encode('utf-8')).hexdigest()
    print(md51)
    if r.exists(md51):
        value = r.get(md51)
        return jsonify({"code": 200, "message": "获取资源成功", "data": value.decode('utf-8')})
    with r.lock("lock", blocking_timeout=10):
        resorce = retryGetResource(url)
        if resorce:
            r.set(md51, resorce,ex=60*10)
            return jsonify({"code": 200, "message": "获取资源成功", "data": resorce})
        else:
            return jsonify({"code": 404, "message": "bad request ", "data": ""})


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host="0.0.0.0", port=8899, debug=False)
