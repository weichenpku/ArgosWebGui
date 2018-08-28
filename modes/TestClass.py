try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil

IrisUtil.GUI.log("hello")

def test():
    print("haha")

class TestClass:
    Title = "hah"  # this is the mode string shown in GUI, if not applied, will not show in GUI

    def __init__(self):
        print("__init__ called")

test()
if __name__ == "__main__":
    test()
