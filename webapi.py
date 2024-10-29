from time import sleep

import requests
import time
import qrcode
import uuid
import time
import json
import queue
import os
import uvicorn
import base64
import pymysql.cursors
import websockets
import asyncio

from fastapi import FastAPI
from fastapi.responses import FileResponse

from threading import Thread, Lock, enumerate
import threading

#线程锁
app = FastAPI()
msglist = queue.Queue()
mutex = Lock()
terminate_flag=False
uid = uuid.uuid4().hex #生成唯一id
uid22=str(uuid.uuid4())
uid33=str(uuid.uuid4())
session = requests.Session()
finderUsername=''
txvideo_nickname=''
txvideo_headImgUrl=''
wx_nickname=''
wx_username=''
wx_encryptedHeadImage=''
adminNickname=''
fansCount=0
uniqId=''
authKey=""
X_Wechat_Uin=""
liveObjectId=""
liveId=""
live_description=""
liveCookies=""

uid2 = {}
finderUsername2 = {}
X_Wechat_Uin2 = {}
liveObjectId2 = {}
liveId2 = {}
live_description2 = {}
liveCookies2 = {}
authKey2 = {}
session2 = {}
stop_events = {}  # 用于存储每个 live_id 对应的停止事件

def filtertime():
    # 获取今天0点的时间戳
    today = time.time()
    filterEndTime = int(today) - (int(today) % 86400)

    # 减去 8664 天
    diff_days = 8664
    filterStartTime = filterEndTime - (diff_days * 86400)

    print("今天0点的时间戳：", filterEndTime)
    print("相减后的时间戳：", filterStartTime)    
    return filterEndTime,filterStartTime


def setcoockis(response):
    # 获取返回的cookie值
    cookies = response.cookies
    # 打印cookie值
    for cookie in cookies:
        print(cookie.name, cookie.value)

def generate_timestamp(length=10):
    current_time = time.time()
    if length == 10:
        timestamp = int(current_time)
    elif length == 13:
        timestamp = int(current_time * 1000)
    else:
        raise ValueError("Invalid timestamp length. Must be 10 or 13.")
    return  str(timestamp)

#获取登录二维码
def getrcode(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_code"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": "0000000000",
        "finger-print-device-id": uid,
        "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    data = {
        "timestamp": str(int(time.time() * 1000)),  # 使用13位时间戳
        "_log_finder_uin": "",
        "_log_finder_id": "",
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session2[live_id].post(url, headers=headers, json=data)
    #setcoockis(response)
    redata=response.json()

    print(f'getrcode_errMesg:{redata["errMsg"]}')

    if 'token' in redata['data']:
        return redata['data']['token']

    return ''

def request_qrcode(retoken, live_id):
    url = f"https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_login_status?token={retoken}&timestamp={generate_timestamp(13)}&_log_finder_uin=&_log_finder_id=&scene=7&reqScene=7"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/login-for-iframe?dark_mode=true&host_type=1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": "0000000000",
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    count = 0
    status= 0
    acctStatus = 0
    while count < 200:
        response = session2[live_id].post(url, headers=headers)
        #setcoockis(response)
        rejson=response.json()
        if rejson['errCode'] == 0:
            # 处理返回的数据
            # ...
            status=rejson['data']['status']
            acctStatus=rejson['data']['acctStatus']
            if status==0 and acctStatus==0:
                print(live_id)
                print('请使用<微信>扫码登录！')
            elif status==5 and acctStatus==1:
                print('已扫码请在手机上点击确认登录！')
            elif status==1 and acctStatus==1:
                print('已成功登录！')
                break
            elif status==3 and acctStatus==0:
                print('已成功登录！')
                break
            else:
                print(rejson)
                print('超时或网络异常已退出')
                break

            count += 1
            time.sleep(1)
        else:
            print("请求失败")
            break

    if count >= 200:
        print("二维码已超时")
    if status==1 & acctStatus==1:
        return True
    return False


def auth_data(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/auth/auth_data"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/login",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": "0000000000",
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": "",
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session2[live_id].post(url, headers=headers, json=data)
    #setcoockis(response)
    rejson=response.json()
    #print(response.json())
    if rejson['errCode'] == 0:
        global wx_encryptedHeadImage
        wx_encryptedHeadImage=rejson['data']['userAttr']['encryptedHeadImage']
        global wx_nickname
        wx_nickname=rejson['data']['userAttr']['nickname']
        global wx_username
        wx_username=rejson['data']['userAttr']['username']
        global txvideo_headImgUrl
        txvideo_headImgUrl=rejson['data']['finderUser']['headImgUrl']
        global txvideo_nickname
        txvideo_nickname=rejson['data']['finderUser']['nickname']
        global finderUsername2
        # finderUsername=rejson['data']['finderUser']['finderUsername']
        finderUsername2[live_id] = rejson['data']['finderUser']['finderUsername']
        return True
    else:
        print("登录异常："+rejson['errMsg'])
        return False


def helper_upload_params(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/helper/helper_upload_params"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/login",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": "0000000000",
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session2[live_id].post(url, headers=headers, json=data)
    rejson=response.json()
    if rejson['errCode'] == 0:
        global authKey2
        # authKey=rejson['data']['authKey']
        authKey2[live_id] = rejson['data']['authKey']
        global X_Wechat_Uin2
        # X_Wechat_Uin=str(rejson['data']['uin'])
        X_Wechat_Uin2[live_id] = str(rejson['data']['uin'])
        return True
    else:
        return False



def check_live_status(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/check_live_status"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/home",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("check_live_status")
    try:
        response = session2[live_id].post(url, headers=headers, json=data,timeout=30)

        rejson=response.json()
        if rejson['errCode'] == 0:
            global liveId2
            # liveId=rejson['data']['liveId']
            liveId2[live_id] = rejson['data']['liveId']
            global live_description2
            # live_description=rejson['data']['description']
            live_description2[live_id]=rejson['data']['description']
            global liveObjectId2
            # liveObjectId=rejson['data']['liveObjectId']
            liveObjectId2[live_id] = rejson['data']['liveObjectId']
            #print("check_live_status end")
            if rejson['data']['status']==1:
                print(f'直播间【{live_description2[live_id]}】状态正常')
            else:
                print(f'直播间【{live_description2[live_id]}】状态={str(rejson["data"]["status"])}')
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        print("check_live_status请求超时了")
        return True

#获取历史直播场次的记录。这里可以不用调用
def get_live_history():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/get_live_history"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/home",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin,
        "finger-print-device-id": uid,
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    request=filtertime()
    filterEndTime,filterStartTime=request
    #查询的开始和结束时间
    data = {
        "pageSize": 1,
        "currentPage": 1,
        "reqType": 2,
        "filterStartTime": filterStartTime,
        "filterEndTime": filterEndTime,
        "timestamp":generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session.post(url, headers=headers, json=data)

    rejson=response.json()
    if rejson['errCode'] == 0:
        return True
    else:
        return False

#
def get_live_info(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/get_live_info"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "liveObjectId": liveObjectId2[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    print('get_live_info param :'+liveObjectId2[live_id]+'-------'+finderUsername2[live_id])
    try:
        response = session2[live_id].post(url, headers=headers, json=data,timeout=30)

        rejson=response.json()
        if rejson['errCode'] == 0:
            return True
        else:
            print(f"get_live_info异常：{rejson}")
            return False
    except requests.exceptions.Timeout:
        print("get_live_info请求超时了")
        return True

#获取msg消息刷新cookie
def join_live(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/join_live"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId2[live_id],
        "finderUsername": finderUsername2[live_id],
        "liveId": liveId2[live_id],
        "timestamp": str(int(time.time() * 1000)), # 使用当前的时间戳
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session2[live_id].post(url, headers=headers, json=data)

    rejson=response.json()
    if rejson['errCode'] == 0:
        global liveCookies2
        # liveCookies=rejson['data']['liveCookies']
        liveCookies2[live_id] = rejson['data']['liveCookies']
        return True
    else:
        print(f"join_live异常：{rejson}")
        return False

#获取最新在线人员信息
def a_online_member(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/online_member"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId2[live_id],
        "finderUsername": finderUsername2[live_id],
        "clearRecentRewardHistory": True,
        "liveId": liveId2[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    try:
        response = session2[live_id].post(url, headers=headers, json=data,timeout=30)
        rejson=response.json()
        if rejson['errCode'] == 0:
            json_str = json.dumps(rejson)
            # 将 JSON 字符串写入本地文件
            with open("online_member.json", "w") as file:
                file.write(json_str)
            return True
        else:
            print(f"online_member异常：{rejson}")
            return False
    except requests.exceptions.Timeout:
        print("online_member请求超时")
        return True

def msg(live_id):
    global liveCookies2
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/msg"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    data = {
        "objectId": liveObjectId2[live_id],
        "finderUsername": finderUsername2[live_id],
        "liveCookies": liveCookies2[live_id],
        "liveId": liveId2[live_id],
        "longpollingScene": 0,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    try:
        response = session2[live_id].post(url, json=data, headers=headers,timeout=30)
        rejson=response.json()
        if rejson['errCode'] == 0:
            #对本次的消息进行解析
            liveCookies2[live_id]=rejson['data']['liveCookies']
            handle_msg(rejson['data'])
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        print("msg请求超时了")
        return True

def reward_gains(live_id):
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/reward_gains"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin2[live_id],
        "finger-print-device-id": uid2[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId2[live_id],
        "finderUsername": finderUsername2[live_id],
        "clearRecentRewardHistory": True,
        "liveId": liveId2[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername2[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("reward_gains")
    try:
        response = session2[live_id].post(url, headers=headers, json=data,timeout=30)
        rejson=response.json()

        if rejson['errCode'] == 0:
            return True
        else:
            print('reward_gains_err:')
            print(rejson)
            return False
    except requests.exceptions.Timeout:
        print("reward_gains请求超时了")
        return True

def gift_enum_list():
    url = "https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/live/gift_enum_list"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://channels.weixin.qq.com",
        "Referer": "https://channels.weixin.qq.com/platform/live/liveBuild",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "X-WECHAT-UIN": X_Wechat_Uin,
        "finger-print-device-id": uid,
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId,
        "username": finderUsername,
        "liveId": liveId,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername,
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    
    response = session.post(url, headers=headers, json=data)
    rejson=response.json()
    print("gift_enum_list:")
    print(data)
    print(rejson)
    if rejson['errCode'] == 0:
        return True
    else:
        return False


def handle_msg(rejson):
    #解析数据
    insert_data = []
    for member in rejson['msgList']:
        if member['type']==1 :
            nickname = member['nickname']
            content = member['content']
            print("昵称："+nickname+"  弹幕信息："+content)
            insert_data.append((9527, content, "", "[]"))
    # 入库
    insert(insert_data)

def getmsg(stop_event, live_id):
    while not stop_event.is_set():
        count = 0
        global terminate_flag
        while not terminate_flag:
            print('get msg live id = '+str(live_id))
            count += 1
            #print("当前时间：", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if get_live_info(live_id) and msg(live_id):
                    time.sleep(0.1)
            else:
                break

            if count % 3 == 0:
                if check_live_status(live_id) and a_online_member(live_id) and reward_gains(live_id):
                    time.sleep(0.1)
                else:
                    break

@app.get("/getmsg")
def getmsgs():
    msglist_dir = "msglist"  # 指定目录路径

    # 检查目录是否存在
    if not os.path.exists(msglist_dir):
        return {"code": 0, "message": "目录不存在"}

    # 获取目录下的所有文件
    files = os.listdir(msglist_dir)

    # 检查是否有文件
    if len(files) == 0:
        return {"code": 0, "message": "目前没有消息"}

    # 取第一个文件
    first_file = files[0]

    # 构建文件路径
    file_path = os.path.join(msglist_dir, first_file)

    # 读取文件内容
    with open(file_path, "r") as file:
        file_content = file.read()

    # 删除已读取的文件
    os.remove(file_path)

    # 返回文件内容
    return {"code": 1, "message": "读取成功", "data": json.loads(file_content)}


@app.get("/clsmsg")
def clear_messages():
    msglist_dir = "msglist"  # 指定目录路径

    # 检查目录是否存在
    if not os.path.exists(msglist_dir):
        return {"code":0,"message": "目录不存在"}

    # 获取目录下的所有文件
    files = os.listdir(msglist_dir)

    # 删除目录下的所有文件
    for file in files:
        file_path = os.path.join(msglist_dir, file)
        os.remove(file_path)

    return {"code":1,"message": "所有文件已删除"}

@staticmethod
def create_connection():
    return pymysql.connect(
        host='127.0.0.1',
        user='admin',
        password='123456',
        database='omnibot',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True  # 设置自动提交模式
    )

@app.get("/get_online_member")
async def get_online_members():
    return FileResponse("online_member.json")

def insert(data):
    db = create_connection()
    sql_insert = "INSERT INTO comments (live_id, content, answer, citations) VALUES (%s, %s, %s, %s)"
    try:
        with db.cursor() as cursor:
            try:
                cursor.executemany(sql_insert, data)
            except Exception as e:
                # 捕获异常
                print(f"插入时发生错误：{e}")
    finally:
        db.close()

def get_live_message(live_id):
    # 为这个 live_id 创建一个新的停止事件
    stop_event = threading.Event()
    stop_events[live_id] = stop_event

    global uid2
    uid2[live_id] = uuid.uuid4().hex

    global session2
    session2[live_id] = requests.Session()

    retoken = getrcode(live_id)
    rehttp = f'https://channels.weixin.qq.com/mobile/confirm_login.html?token={retoken}'

    qr = qrcode.QRCode()
    qr.border = 1
    qr.add_data(rehttp)
    qr.make()
    qr.print_ascii(out=None, tty=False, invert=False)

    print('请使用<微信>扫码登录！')

    time.sleep(1)

    # 获取二维码以及前期一系列准备工作。
    if request_qrcode(
            retoken, live_id) and auth_data(live_id) and helper_upload_params(live_id) and check_live_status(live_id) and get_live_info(live_id) and join_live(live_id) and a_online_member(live_id):
        print("加载成功，开启消息获取线程。获取实时弹幕消息。")
        threading.Thread(target=getmsg, args=(stop_event, live_id)).start()

async def ws_path(websocket, path):
    if path == "/start":
        async for data_json in websocket:
            data = json.loads(data_json)

            try:
                # threading.Thread(target=get_live_message, args=(data["live_id"],)).start()
                get_live_message(data["live_id"])
            except Exception as e:
                print(f"Error in get_live_message_two: {e}")

            print(f"Received message: {data["live_id"]}")
            # 将接收到的消息发送回客户端
            # await websocket.send(f"Server received: {data["live_id"]}")

            if websocket.closed:
                # 设置停止事件以停止线程
                stop_event = stop_events.get(data["live_id"])
                if stop_event:
                    stop_event.set()
                return

async def ws_start():
    # 使用 websockets.serve 创建WebSocket服务，指定处理函数和监听地址、端口
    async with websockets.serve(ws_path, "localhost", 8765):
        # 这会让服务器一直运行
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(ws_start())