
from .plot_learning_curve import PlotLearningCurve
import tensorflow.keras as keras

class KerasLearningCurve(keras.callbacks.Callback):
    """Keras.callback interface to draw learning curve

    This attempts to dynamically construct a learning curve plot
    based on the keras model configuration. This depends on `metrics`
    in `model.compile()`, `epochs` and `validation_data` in
    `model.fit()`.

    Example:
        model.fit(x_train, y_train,
                  batch_size=128,
                  epochs=20,
                  validation_data=(x_test, y_test),
                  callbacks=[KerasLearningCurve()],
                  verbose=0)

    Arguments:
        draw_every: Only update the plot every `draw_interval` epoch. This
            can be useful on a remote connection, where data transfer between
            server and client might be slow.
        **kwargs: forwarded to PlotLearningCurve, the defaults
            are infered from the keras model configuration, or mappings
            if mappings is defined.
    """
    def __init__(self, draw_interval=1, **kwargs):
        if not isinstance(draw_interval, int) or draw_interval <= 0:
            raise ValueError('draw_interval must be a positive integer')

        self._draw_interval = draw_interval
        self._kwargs = kwargs

        self._observed_metrics = set()
        self._dynamic = True
        self._plotter = None

        if 'mappings' in self._kwargs:
            self._dynamic = False
            self._initialize_plotter()

    def _infer_settings(self,
                        mappings=None,
                        line_config=None,
                        facet_config=None,
                        xaxis_config=None,
                        **kwargs):
        # Dynamically set max_epoch, if not specified
        if xaxis_config is None:
            xaxis_config = dict()
        if 'name' not in xaxis_config:
            xaxis_config['name'] = 'Epoch'
        if 'limit' not in xaxis_config:
            xaxis_config['limit'] = [0, None]
        if xaxis_config['limit'][1] is None:
            xaxis_config['limit'][1] = self.params['epochs'] - 1

        # Dynamically infer mappings
        if mappings is None:
            mappings = { key:dict() for key in self._observed_metrics }
        for mapping_key, mapping_def in mappings.items():
            infered_facet, infered_line = (mapping_key, 'train')
            if mapping_key.startswith('val_'):
                infered_facet, infered_line = (mapping_key[4:], 'validation')

            if 'line' not in mapping_def:
                mapping_def['line'] = infered_line
            if 'facet' not in mapping_def:
                mapping_def['facet'] = infered_facet

        # Dynamically infer line_config
        if line_config is None:
            line_config = { mapping_def['line']:dict() for mapping_def in mappings.values() }
        for line_key, line_def in line_config.items():
            if line_key == 'train':
                infered_name, infered_color = ('Train', '#F8766D')
            elif line_key == 'validation':
                infered_name, infered_color = ('Validation', '#00BFC4')
            else:
                infered_name, infered_color = (line_key, '#333333')

            if 'name' not in line_def:
                line_def['name'] = infered_name
            if 'color' not in line_def:
                line_def['color'] = infered_color

        # Dynamically infer facet_config
        if facet_config is None:
            facet_config = { mapping_def['facet']:dict() for mapping_def in mappings.values() }
        for facet_key, facet_def in facet_config.items():
            if facet_key == 'loss':
                infered_name, infered_limit, infered_scale = ('Loss', [None, None], 'log10')
            elif facet_key in {'acc', 'accuracy', 'binary_accuracy', 'categorical_accuracy', 'sparse_categorical_accuracy'}:
                infered_name, infered_limit, infered_scale = ('Accuracy', [0, 1], 'linear')
            elif facet_key == 'lr':
                infered_name, infered_limit, infered_scale = ('Learning Rate', [0, None], 'linear')
            else:
                infered_name, infered_limit, infered_scale = (facet_key, [None, None], 'linear')

            if 'name' not in facet_def:
                facet_def['name'] = infered_name
            if 'limit' not in facet_def:
                facet_def['limit'] = infered_limit
            if 'scale' not in facet_def:
                facet_def['scale'] = infered_scale

        return {
            'mappings': mappings,
            'line_config': line_config,
            'facet_config': facet_config,
            'xaxis_config': xaxis_config,
            **kwargs
        }

    def _initialize_plotter(self):
        settings = self._infer_settings(**self._kwargs)
        if self._plotter is None:
            self._plotter = PlotLearningCurve(**settings)
        else:
            self._plotter.reconfigure(**settings)

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        if self._dynamic and len(logs.keys() - self._observed_metrics) > 0:
            self._observed_metrics.update(logs.keys())
            self._initialize_plotter()

        self._plotter.append(epoch, logs)

        # Update plot
        if epoch % self._draw_interval == 0:
            self._plotter.draw()

    def on_train_end(self, logs=None):
        if self._plotter is not None:
            self._plotter.finalize()
