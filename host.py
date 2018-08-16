"""
本程序为控制Argos系统的服务器端程序，推荐运行在网络靠近Argos的一侧，而用户可以使用网页进行操控（支持多用户同时操作）以及查看数据图像
written by wy@180802
"""

import time, main, GUI

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
        gains = main.IrisObj.nowGains()
        ret["gainStructure"] = gains["list"]
        nowGain = main.IrisObj.nowGains()
        data = gains["data"]
        for gainKey in data:
            ret['userSettings']['GainSettings-%s' % gainKey] = data[gainKey]  # 把设置加入进去
    else:
        ret["gainStructure"] = []
    ret['userSettings']['BasicSettings-RunMode'] = main.mode
    ret['availableModes'] = main.availableModes  # tell user about this
    return ret

def userClickButton(button):  # 用户点击按钮事件
    if button == 'reset':
        if main.state == "stopped":
            main.IrisCount = 0
            main.IrisSerialNums = []
            sendSettingsToUser()
        else:
            GUI.error("cannot reset in no \"stopped\" state")
    elif button == 'init':
        if main.state == "stopped":
            main.state = "run-pending"
    elif button == 'stop':
        if main.state == "running":
            main.state = "stop-pending"
    elif button == 'trig' or button == 'AutoTrig':
        main.userTrig = True

def userSyncSettings(settings):
    if 'BasicSettings-IrisCount' in settings:
        if main.state == 'stopped':
            IrisCounttar = int(settings['BasicSettings-IrisCount'])
            if (IrisCounttar > main.IrisCount):
                for i in range(IrisCounttar - main.IrisCount): main.IrisSerialNums.append('SERIAL-0-Rx-0')
            elif (IrisCounttar < main.IrisCount):
                main.IrisSerialNums = main.IrisSerialNums[:IrisCounttar]  # 裁切
            main.IrisCount = IrisCounttar
        else:
            GUI.error('cannot set BasicSettings-IrisCount in no \"stopped\" state')
    for key in settings:
        if key[:len("BasicSettings-IrisDevices-")] == "BasicSettings-IrisDevices-":
            if main.state == 'stopped':
                idx = int(key[len("BasicSettings-IrisDevices-"):])
                if idx >= 0 and idx < len(main.IrisSerialNums):
                    main.IrisSerialNums[idx] = settings[key]
            else:
                GUI.error('cannot set BasicSettings in no \"stopped\" state')
        elif key == "BasicSettings-RunMode":
            if main.state == 'stopped':
                main.mode = settings[key]
            else:
                GUI.error('cannot set RunMode in no \"stopped\" state')
        elif key[:len("GainSettings-")] == "GainSettings-":
            main.gainModified.enqueue(key[len("GainSettings-"):], settings[key])  # just enqueue, but not set gain directly, for safety!



# flask服务器框架，本部分只包含通信，不包含任何逻辑
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging, json
app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app=app)
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 设置不输出GET请求之类的信息，只输出error，保证控制台干净

def maincall():
    global loopDelay
    GUI.log('main function start at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    main.setup()
    GUI.log('setup finished at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    while True:
        main.loop(socketio.sleep)
        socketio.sleep(main.loopDelay)

@app.route("/")
def index():
    return app.send_static_file('index.html')
@app.route('/save.json')
def save():
    return jsonify(nowSettings()["userSettings"])
@app.route('/load', methods=['POST'])
def load():
    f = request.files['file']
    st = str(f.read(), encoding="utf-8")
    try:
        js = json.loads(st)
        main.gainModified.clear()  # first clear the queue, in case user load file for twice or more!
        userSyncSettings(js)
        sendSettingsToUser()
        GUI.alert('config "%s" has been loaded' % f.filename)
    except json.decoder.JSONDecodeError:
        GUI.error('json file format error')
    return 'haha'
@socketio.on('connect')
def ws_connect():
    GUI.log('socketio %s connect    at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    sendSettingsToUser()
@socketio.on('disconnect')
def ws_disconnect():
    GUI.log('socketio %s disconnect at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
@socketio.on('button')
def ws_button(button):
    if button != "AutoTrig":  # to avoid lots of output log!
        GUI.log('user %s click button: %s' % (request.remote_addr, button))
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
            main.extraInfosReady = False
            socketio.emit('extraInfos', main.extraInfos, broadcast=True)
socketio.start_background_task(timerSendUpdatedStateToUsers)
if __name__=='__main__':
    GUI.registerSocketIO(socketio)  # enable GUI socketio
    socketio.run(app, host='0.0.0.0', port=8080)
