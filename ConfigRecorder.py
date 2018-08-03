"""
记录当前配置，当新配置修改的时候，能够获取被改变的字段；保证顺序，对同一个键重复设置值则只保留最后一个
保证线程安全性 wy@180802
"""

import threading

class ConfigRecorder:
    def __init__(self, initDict={}):
        self.mutex = threading.Lock()  # 创建一个线程锁，保证线程安全
        self.dict = initDict  # 创建字典
        self.modified = []  # 存储被修改了的key
    
    def __contains__(self, key):  # 重载in关键字
        return key in self.dict
    
    def modify(self, key, value):
        if key not in self.dict:
            return "Error: Key not exist"
        self.mutex.acquire()  # 上锁保证线程安全
        if key in self.modified:
            self.modified.remove(key)  # 保证顺序，如果多次设置只保留最后一次
            return ("Warning: Key (%s) has been modified, only reserve the last one" % key)
        self.modified.append(key)
        self.dict[key] = value
        self.mutex.release()
        return None

    def getModifiedKeyValuePair(self, clear=False):  # 如果clear为True的话，下一次get就不包含之前的了
        if len(self.modified) == 0:
            return []
        self.mutex.acquire()  # 上锁保证线程安全
        ret = []
        for key in self.modified:
            ret.append((key, self.dict[key]))
        if clear:
            self.modified = []  # 清空
        self.mutex.release()
        return ret


