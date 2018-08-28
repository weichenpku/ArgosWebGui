"""
put public functions here

you should write functions in your class first, if you think they're really common one and should be share, put them here
the function should like this:
    def something(self, foo, bar):
        pass
this make sure that all classes can use these functions, just like their own class function
"""

# import parent folder's file
try:
    import GUI
except Exception as e:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import GUI

GUI.log('IrisUtil is loaded')

def EVENT_trigger_do_nothing(self):
    print('haha')
    GUI.log('haha')
