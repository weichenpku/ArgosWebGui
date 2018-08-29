import time, threading


class ModifyQueue:
    def __init__(self):
        self.mutex = threading.Lock()
        self.queue = []

    def enqueue(self, key, value):
        self.mutex.acquire()
        self.queue.append((key, value))
        self.mutex.release()
    
    def empty(self):
        return len(self.queue) == 0
    
    def clear(self):
        self.mutex.acquire()
        self.queue.clear()
        self.mutex.release()
    
    def dequeue(self):
        self.mutex.acquire()
        ret = self.queue.pop(0)
        self.mutex.release()
        return ret

class LoopTimer:
    def __init__(self, func, timeMs, Always=False, running=True):
        self.timeMs = timeMs
        self.func = func
        self.running = running
        self.Always = Always
        self.time = time.time()
    
    def loop(self):
        if self.running and (time.time() - self.time) * 1000 >= self.timeMs:  # 该调用了
            self.func(self)  # 把自己的参数传入，可以在里面控制
            if self.Always:
                self.time = time.time()
            else:
                self.running = False

    def restart(self):
        self.time = time.time()
        self.running = True
    
    def stop(self):
        self.running = False
