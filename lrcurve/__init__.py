
from .plot_learning_curve import PlotLearningCurve

try:
    import tensorflow.keras as keras
    from .keras_learning_curve import KerasLearningCurve
except ModuleNotFoundError as e:
    save_error = e
    class KerasLearningCurve:
        def __init__(self):
            raise save_error
