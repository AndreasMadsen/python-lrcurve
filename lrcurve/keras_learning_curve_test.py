from nose.tools import *

from lrcurve import KerasLearningCurve

class DisplayHandle:
    def __init__(self, display_objects):
        self.display_objects = display_objects

    def update(self, obj):
        self.display_objects.append(obj)

def display_replacer(display_objects):
    def display(obj, display_id=None):
        display_objects.append(obj)
        return DisplayHandle(display_objects)
    return display

def test_crude_sanity_check():
    # Unfortunetly the notebooks are really the best way to test if
    # things are working.
    plot = KerasLearningCurve(display_fn=display_replacer([]))

@raises(ValueError)
def test_draw_interval_is_not_positive_number():
    KerasLearningCurve(
        draw_interval=0,
        display_fn=display_replacer([])
    )
