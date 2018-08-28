"""
put public functions here

you should write functions in your class first, if you think they're really common one and should be share, put them here
the function should like this:
    def something(self, foo, bar):
        pass
this make sure that all classes can use these functions, just like their own class function
"""
import sys
sys.path.append(".")  # make parent folder import enabled
from modes import *

def EVENT_trigger_do_nothing(self):
    print('haha')
    GUI.log('haha')
