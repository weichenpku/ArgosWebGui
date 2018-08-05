"""
本程序为控制Argos系统的服务器端程序，推荐运行在网络靠近Argos的一侧，而用户可以使用网页进行操控（支持多用户同时操作）以及查看数据图像
written by wy@180802
"""

import time

import main

def nowSettings():  # 用户想获取当前的系统信息，返回一个字典
    ret = {
        'version': main.version,
        'state': main.state,
        'userSettings': {  # 这部分是直接和html挂钩的
            'BasicSettings-IrisCount': main.IrisCount
        }
    }
    assert main.IrisCount == len(main.IrisSerialNums)  # 他们应当长度相同的
    for i in range(main.IrisCount):
        ret['userSettings']['BasicSettings-IrisDevices-%d' % i] = main.IrisSerialNums[i]
    if main.IrisObj is not None:
        ret['availableRxGains'] = main.IrisObj.availableRxGains()
        ret['availableTxGains'] = main.IrisObj.availableTxGains()
        nowGainRx, nowGainTx = main.IrisObj.nowGains()
        for i,ele in enumerate(nowGainRx):
            for gainKey in ele:
                ret['userSettings']['GainSettings-Rx-%d-%s' % (i, gainKey)] = ele[gainKey]  # 把设置加入进去
        for i,ele in enumerate(nowGainTx):
            for gainKey in ele:
                ret['userSettings']['GainSettings-Tx-%d-%s' % (i, gainKey)] = ele[gainKey]  # 把设置加入进去
    else:
        ret['availableRxGains'] = []
        ret['availableTxGains'] = []
    return ret

def userClickButton(button):  # 用户点击按钮事件
    if button == 'test':
        main.IrisCount = 2
        main.IrisSerialNums = ['hahaha', 'ijijiji']
        sendSettingsToUser()
    elif button == 'init':
        if main.state == "stopped":
            main.state = "run-pending"
    elif button == 'stop':
        if main.state == "running":
            main.state = "stop-pending"
    elif button == 'trig':
        main.userTrig = True

def userSyncSettings(settings):
    if 'BasicSettings-IrisCount' in settings:
        if main.state == 'stopped':
            IrisCounttar = int(settings['BasicSettings-IrisCount'])
            if (IrisCounttar > main.IrisCount):
                for i in range(IrisCounttar - main.IrisCount): main.IrisSerialNums.append('')
            elif (IrisCounttar < main.IrisCount):
                main.IrisSerialNums = main.IrisSerialNums[:IrisCounttar]  # 裁切
            main.IrisCount = IrisCounttar
        elif main.state == 'running':
            print('Error: cannot set BasicSettings-IrisCount when running')
    for key in settings:
        if key[:len("BasicSettings-IrisDevices-")] == "BasicSettings-IrisDevices-" and main.state == 'stopped':
            idx = int(key[len("BasicSettings-IrisDevices-"):])
            if idx >= 0 and idx < len(main.IrisSerialNums):
                main.IrisSerialNums[idx] = settings[key]







# flask服务器框架，本部分只包含通信，不包含任何逻辑
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app=app)
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 设置不输出GET请求之类的信息，只输出error，保证控制台干净

def maincall():
    global loopDelay
    print('main function start at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    main.setup()
    print('setup finished at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    while True:
        main.loop()
        socketio.sleep(main.loopDelay)

@app.route("/")
def index():
    return app.send_static_file('index.html')
@socketio.on('connect')
def ws_connect():
    print('socketio %s connect    at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    sendSettingsToUser()
@socketio.on('disconnect')
def ws_disconnect():
    print('socketio %s disconnect at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
@socketio.on('button')
def ws_button(button):
    print('user %s click button: %s' % (request.remote_addr, button))
    userClickButton(button)  # 逻辑层
    sendSettingsToUser()
@socketio.on('syncSettings')
def ws_syncSettings(settings):
    userSyncSettings(settings)
    sendSettingsToUser()
def sendSettingsToUser():
    settings = nowSettings()  # 逻辑层的事情
    socketio.emit('settings', settings, broadcast=True)
socketio.start_background_task(maincall)
def timerSendUpdatedStateToUsers():
    while True:
        socketio.sleep(0.3)
        if main.changed:
            main.changed = False
            sendSettingsToUser()
        if main.sampleDataReady:
            main.sampleDataReady = False
            socketio.emit('samples', main.sampleData, broadcast=True)
        if main.extraInfosReady:
            socketio.emit('extraInfos', main.extraInfos, broadcast=True)
socketio.start_background_task(timerSendUpdatedStateToUsers)
if __name__=='__main__':
    socketio.run(app, host='0.0.0.0', port=80)
