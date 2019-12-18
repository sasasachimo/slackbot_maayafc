import boto3
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import slackweb
import datetime
import pickle
import configparser
import os

ini = configparser.SafeConfigParser()
ini.read("./config.ini")

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    bucket = 'maaya-fc-top'
    key = 'new_atcl.txt'
    file_path = '/tmp/new_atcl.txt'
    try:
        bucket = s3.Bucket(bucket)
        bucket.download_file(key, file_path)
        print('download_ok')
    except Exception as e:
        print(e)

    # メールアドレスとパスワードの指定
    USER = ini.get("maaya_fc", "username")
    PASS = ini.get("maaya_fc", "password")

    # セッションを開始
    session = requests.session()

    # ログイン
    login_info = {
        "log":USER,
        "pwd":PASS,
        "testcookie":"0"
    }

    # action
    url_login = "https://maaya-fc.jp/login/"
    res = session.post(url_login, data=login_info)
    res.raise_for_status() # エラーならここで例外を発生させる

    soup = BeautifulSoup(res.text, "html.parser")

    columns = [t.text for t in soup("span", class_="home-news__title")]
    url = [tag['href'] for tag in soup('a', class_="home-news__link")]
    newest_list = columns[0:3],url[0:3]

    newatcl_cnt = 0
    f = open(file_path, "rb")
    newest_list_stock = pickle.load(f)
    f.close()

    for atcl_num in range(len(newest_list[0])):
        if newest_list[0][atcl_num] == newest_list_stock[0][0]:
            break
        else:
            newatcl_cnt = newatcl_cnt + 1
    if newatcl_cnt > 0:
        f = open(file_path, 'wb')
        pickle.dump(newest_list, f)
        f.close()
        bucket.upload_file(file_path, key)

    if newatcl_cnt == 0:
        print(datetime.datetime.now())
        print("更新なし")
    else:
        slack = slackweb.Slack(url=ini.get("maaya_fc", "slackurl"))
        
    for newatcl_num in range(newatcl_cnt):
        if newest_list[1][newatcl_num] not in 'https://maaya-fc.jp/':
	        newest_list[1][newatcl_num] = 'https://maaya-fc.jp/' + newest_list[1][newatcl_num]
        slack.notify(text = newest_list[0][newatcl_num] + ':' + newest_list[1][newatcl_num])
        print(newest_list[0][newatcl_num] + ':' + newest_list[1][newatcl_num])