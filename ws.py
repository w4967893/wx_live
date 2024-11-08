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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from threading import Thread, Lock, enumerate
import threading
from io import BytesIO

#线程锁
app = FastAPI()
terminate_flag = {}
tx_video_nickname = {}
tx_video_headImgUrl = {}
wx_nickname = {}
wx_username = {}
wx_encryptedHeadImage = {}
uid = {}
finderUsername = {}
X_Wechat_Uin = {}
liveObjectId = {}
liveId = {}
live_description = {}
liveCookies = {}
authKey = {}
session = {}
stop_events = {}  # 用于存储每个 live_id 对应的停止事件
live_websockets = {}

def stop_thread(live_id):
    if live_id not in stop_events:
        return False
    # 设置 Event 对象，通知线程应该停止
    stop_events[live_id].set()
    del stop_events[live_id]
    return True

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
        "finger-print-device-id": uid[live_id],
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

    response = session[live_id].post(url, headers=headers, json=data)
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
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    count = 0
    status= 0
    acctStatus = 0
    while count < 200:
        response = session[live_id].post(url, headers=headers)
        #setcoockis(response)
        rejson=response.json()
        if rejson['errCode'] == 0:
            # 处理返回的数据
            # ...
            status=rejson['data']['status']
            acctStatus=rejson['data']['acctStatus']
            if status==0 and acctStatus==0:
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
        "finger-print-device-id": uid[live_id],
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

    response = session[live_id].post(url, headers=headers, json=data)
    rejson=response.json()
    if rejson['errCode'] == 0:
        global wx_encryptedHeadImage
        wx_encryptedHeadImage[live_id]=rejson['data']['userAttr']['encryptedHeadImage']
        global wx_nickname
        wx_nickname[live_id]=rejson['data']['userAttr']['nickname']
        global wx_username
        wx_username[live_id]=rejson['data']['userAttr']['username']
        global tx_video_headImgUrl
        tx_video_headImgUrl[live_id]=rejson['data']['finderUser']['headImgUrl']
        global tx_video_nickname
        tx_video_nickname[live_id]=rejson['data']['finderUser']['nickname']
        global finderUsername
        finderUsername[live_id] = rejson['data']['finderUser']['finderUsername']
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
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session[live_id].post(url, headers=headers, json=data)
    rejson=response.json()
    if rejson['errCode'] == 0:
        global authKey
        authKey[live_id] = rejson['data']['authKey']
        global X_Wechat_Uin
        X_Wechat_Uin[live_id] = str(rejson['data']['uin'])
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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    try:
        response = session[live_id].post(url, headers=headers, json=data,timeout=30)

        rejson=response.json()
        if rejson['errCode'] == 0:
            global liveId
            liveId[live_id] = rejson['data']['liveId']
            global live_description
            live_description[live_id]=rejson['data']['description']
            global liveObjectId
            liveObjectId[live_id] = rejson['data']['liveObjectId']
            #print("check_live_status end")
            if rejson['data']['status']==1:
                print(f'直播间【{live_description[live_id]}】状态正常')
            else:
                print(f'直播间【{live_description[live_id]}】状态={str(rejson["data"]["status"])}')
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        print("check_live_status请求超时了")
        return True

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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "liveObjectId": liveObjectId[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    print('get_live_info param :'+liveObjectId[live_id]+'-------'+finderUsername[live_id])
    try:
        response = session[live_id].post(url, headers=headers, json=data,timeout=30)

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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId[live_id],
        "finderUsername": finderUsername[live_id],
        "liveId": liveId[live_id],
        "timestamp": str(int(time.time() * 1000)), # 使用当前的时间戳
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    response = session[live_id].post(url, headers=headers, json=data)

    rejson=response.json()
    if rejson['errCode'] == 0:
        global liveCookies
        liveCookies[live_id] = rejson['data']['liveCookies']
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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId[live_id],
        "finderUsername": finderUsername[live_id],
        "clearRecentRewardHistory": True,
        "liveId": liveId[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    try:
        response = session[live_id].post(url, headers=headers, json=data,timeout=30)
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
    global liveCookies
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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    data = {
        "objectId": liveObjectId[live_id],
        "finderUsername": finderUsername[live_id],
        "liveCookies": liveCookies[live_id],
        "liveId": liveId[live_id],
        "longpollingScene": 0,
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }

    try:
        response = session[live_id].post(url, json=data, headers=headers,timeout=30)
        rejson=response.json()
        if rejson['errCode'] == 0:
            #对本次的消息进行解析
            liveCookies[live_id]=rejson['data']['liveCookies']
            handle_msg(rejson['data'], live_id)
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
        "X-WECHAT-UIN": X_Wechat_Uin[live_id],
        "finger-print-device-id": uid[live_id],
        "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    data = {
        "objectId": liveObjectId[live_id],
        "finderUsername": finderUsername[live_id],
        "clearRecentRewardHistory": True,
        "liveId": liveId[live_id],
        "timestamp": generate_timestamp(13),
        "_log_finder_uin": "",
        "_log_finder_id": finderUsername[live_id],
        "rawKeyBuff": None,
        "pluginSessionId": None,
        "scene": 7,
        "reqScene": 7
    }
    #print("reward_gains")
    try:
        response = session[live_id].post(url, headers=headers, json=data,timeout=30)
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

def handle_msg(rejson, live_id):
    #解析数据
    insert_data = []
    for member in rejson['msgList']:
        if member['type']==1 :
            nickname = member['nickname']
            content = member['content']
            print("昵称："+nickname+"  弹幕信息："+content)
            insert_data.append((live_id, content, "", "[]"))
    # 入库
    insert(insert_data)

def getmsg(stop_event, live_id):
    count = 0
    while not stop_event.is_set():
        print('get msg live id = '+str(live_id))
        print(stop_events)
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
    print(str(live_id)+"线程停止了")

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

def get_live_message(live_id, retoken):
    # 为这个 live_id 创建一个新的停止事件
    stop_event = threading.Event()
    global stop_events
    stop_events[live_id] = stop_event

    # 获取二维码以及前期一系列准备工作。
    if request_qrcode(
            retoken, live_id) and auth_data(live_id) and helper_upload_params(live_id) and check_live_status(live_id) and get_live_info(live_id) and join_live(live_id) and a_online_member(live_id):
        print("加载成功，开启消息获取线程。获取实时弹幕消息。")
        threading.Thread(target=getmsg, args=(stop_event, live_id)).start()
    else:
        return False

@app.get("/api/stop")
async def stop_live(live_id: int | None = None):
    if stop_thread(live_id):
        # 通知所有与该 live_id 关联的 WebSocket 连接
        if live_id in live_websockets:
            await live_websockets[live_id].send_text(json.dumps({"is_ok": True, "data": {"status": 1, "live_id": live_id}}))
            del live_websockets[live_id]
            return {
                "is_ok": True,
                "message": "success"
            }
    return {
        "is_ok": False,
        "message": "Live id 不存在"
    }

@app.websocket("/ws/start")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_json = await websocket.receive_text()
            print("获取到的参数"+str(data_json))
            data = json.loads(data_json)

            # 如果live_id已存在
            if data["live_id"] in stop_events:
                # 因为每次连接websocket都会更改，对本次websocket进行更改
                live_websockets[data["live_id"]]=websocket
                print("该live id已在获取弹幕信息")
                await websocket.send_text(json.dumps({"is_ok": True, "data": {"status": 3, "live_id": data["live_id"]}}))
                # return
            else:
                global uid
                uid[data["live_id"]] = uuid.uuid4().hex

                global sessions
                session[data["live_id"]] = requests.Session()

                retoken = getrcode(data["live_id"])
                rehttp = f'https://channels.weixin.qq.com/mobile/confirm_login.html?token={retoken}'

                qr = qrcode.QRCode()
                qr.border = 1
                qr.add_data(rehttp)
                qr.make()

                # 生成二维码图像
                img = qr.make_image(fill_color="black", back_color="white")

                # 将图像保存到字节流中
                buffer = BytesIO()
                img.save(buffer)
                buffer.seek(0)

                # 编码为Base64字符串
                qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')

                # 发送给客户端
                await websocket.send_text(json.dumps({"is_ok":True, "data": {"status": 2, "live_id": data["live_id"], "qr_base64":qr_base64}}))

                is_success = get_live_message(data["live_id"], retoken)
                if is_success is not None:
                    stop_thread(data["live_id"])
                    # 认证二维码超时，获取视频号信息失败等
                    await websocket.send_text(json.dumps({"is_ok": False, "data": {"status": 1, "live_id": data["live_id"]}}))

                # 添加 WebSocket 到 live_id 的列表中
                if data["live_id"] not in live_websockets:
                    live_websockets[data["live_id"]]=websocket

    except Exception as e:
        print("关闭客户端连接")
        # stop_event = stop_events.get(data["live_id"])
        # print(f"Error in : {e}")
        # if stop_event:
        #     stop_event.set()
        #     del stop_events[data["live_id"]]
        #
        # # 移除 WebSocket 连接
        # if data["live_id"] in live_websockets:
        #     live_websockets[data["live_id"]].remove(websocket)
        #     if not live_websockets[data["live_id"]]:
        #         del live_websockets[data["live_id"]]
        # await websocket.close()
        pass

if __name__ == '__main__':
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=18081, log_level="info", reload=True)
