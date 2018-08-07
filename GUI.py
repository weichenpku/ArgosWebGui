"""
provding functions for user interface
"""

PRINT_TO_STDOUT = True  # whether print to stdout
ALERT_TO_BROWSER = True  # whether use alert to inform user
ERROR_TO_BROWSER = True
LOG_TO_BROWSER = True

import time

socketio = None
def registerSocketIO(socketio_):
    global socketio
    socketio = socketio_

def log(msg):
    global socketio
    if LOG_TO_BROWSER and socketio is not None:
        socketio.emit('log', msg, broadcast=True)
    if PRINT_TO_STDOUT:
        print("Log(%s): " % time.strftime("%H:%M:%S", time.localtime()), msg)

def alert(msg):
    global socketio
    if ALERT_TO_BROWSER and socketio is not None:
        socketio.emit('alert', msg, broadcast=True)
    if PRINT_TO_STDOUT:
        print("Alert(%s): " % time.strftime("%H:%M:%S", time.localtime()), msg)

def error(msg):
    global socketio
    if ERROR_TO_BROWSER and socketio is not None:
        socketio.emit('error', msg, broadcast=True)
    if PRINT_TO_STDOUT:
        print("Error(%s): " % time.strftime("%H:%M:%S", time.localtime()), msg)
