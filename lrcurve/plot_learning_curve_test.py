from nose.tools import *

from lrcurve import PlotLearningCurve

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
    display_objects = []
    plot = PlotLearningCurve(display_fn=display_replacer(display_objects))

    plot.append(0, {
        'loss': {
            'train': 1, 'validation': 0
        }
    })
    plot.draw()

    for i in range(1, 10):
        plot.append(i, {
            'loss': {
                'train': i * 10 + 1,
                'validation': i * 10
            }
        })
    plot.draw()

    plot.finalize()

    assert_equal(len(display_objects), 6)

@raises(ValueError)
def test_height_is_string():
    PlotLearningCurve(
        height = 'string',
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_width_is_string():
    PlotLearningCurve(
        width = 'string',
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_line_config_is_not_dict():
    PlotLearningCurve(
        line_config='string',
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_line_config_is_missing_name():
    PlotLearningCurve(
        line_config={ 'test': { 'color': 'red' } },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_line_config_is_missing_color():
    PlotLearningCurve(
        line_config={ 'test': { 'name': 'name' } },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_facet_config_is_missing_name():
    PlotLearningCurve(
        line_config={ 'loss': { 'limit': [None, None] } },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_facet_config_is_missing_limit():
    PlotLearningCurve(
        line_config={ 'loss': { 'name': 'name' } },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_facet_config_limit_has_wrong_amount_of_elements():
    PlotLearningCurve(
        line_config={ 'loss': { 'name': 'name', 'limit': [] }},
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_facet_config_limit_has_wrong_type():
    PlotLearningCurve(
        line_config={ 'loss': { 'name': 'name', 'limit': ['str', 'str'] }},
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_xaxis_config_is_missing_name():
    PlotLearningCurve(
        xaxis_config={ 'limit': [None, None] },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_xaxis_config_is_missing_limit():
    PlotLearningCurve(
        xaxis_config={ 'name': 'name' },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_xaxis_config_limit_has_wrong_amount_of_elements():
    PlotLearningCurve(
        xaxis_config={ 'name': 'name', 'limit': [] },
        display_fn=display_replacer([])
    )

@raises(ValueError)
def test_facet_config_limit_has_wrong_type():
    PlotLearningCurve(
        xaxis_config={ 'name': 'name', 'limit': ['str', 'str'] },
        display_fn=display_replacer([])
    )
