try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil

def test():
    print("haha")

class SinusoidTransceiver:
    def __init__(self, main):
        self.main = main
    
    def loop(self):
        pass

if __name__ == "__main__":
    test()
