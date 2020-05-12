
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
        metric_mapping: dict that maps metric names to plot facet and
            line. For example:
                metric_mapping = {
                    'loss': { 'facet': 'loss', 'line': 'train' },
                    'val_loss': { 'facet': 'loss', 'line': 'validation' },
               }
            default is `None`, meaning it is infered from the keras model
            configuration.
        draw_every: Only update the plot every `draw_interval` epoch. This
            can be useful on a remote connection, where data transfer between
            server and client might be slow.
        **kwargs: forwarded to PlotLearningCurve, the defaults
            are infered from the keras model configuration.
    """
    def __init__(self, metric_mapping = None, draw_interval=1, **kwargs):
        # argument assertion
        if metric_mapping is not None:
            if not isinstance(metric_mapping, dict):
                raise ValueError('line_config must be a dict')
            for metric_key, metric_description in metric_mapping.items():
                if 'facet' not in metric_description or not isinstance(metric_description['facet'], str):
                    raise ValueError(f'metric_description["{metric_key}"]["facet"] must a string')
                if 'line' not in metric_description or not isinstance(metric_description['line'], str):
                    raise ValueError(f'metric_description["{metric_key}"]["line"] must a string')

        if not isinstance(draw_interval, int) or draw_interval <= 0:
            raise ValueError('draw_interval must be a positive integer')

        self._draw_interval = draw_interval
        self._metric_mapping = metric_mapping
        self._facet_keys = None

        self._kwargs = kwargs
        self._plotter = None

    def _setup_plotter(self, metrics_names):
        do_validation = False

        # Set the metric mapping, if not specified
        if self._metric_mapping is None:
            self._metric_mapping = {}
            for metric_name in metrics_names:
                if metric_name.startswith('val_'):
                    do_validation = True
                    self._metric_mapping[metric_name] = {
                        'facet': metric_name[4:],
                        'line': 'validation'
                    }
                else:
                    self._metric_mapping[metric_name] = {
                        'facet': metric_name,
                        'line': 'train'
                    }

        # pre-compute facet_keys
        self._facet_keys = list(set(
            metric_assigment['facet'] for metric_assigment in self._metric_mapping.values()
        ))

        # Dynamically set max_epoch, if not specified
        if 'xaxis_config' not in self._kwargs or self._kwargs['xaxis_config'] is None:
            self._kwargs['xaxis_config'] = { 'name': 'Epoch', 'limit': [0, None] }
        if 'limit' not in self._kwargs['xaxis_config']:
            self._kwargs['xaxis_config']['limit'] = [0, None]
        if self._kwargs['xaxis_config']['limit'][1] is None:
            self._kwargs['xaxis_config']['limit'][1] = self.params['epochs'] - 1

        # set the line_config, if not specified
        if 'line_config' not in self._kwargs or self._kwargs['line_config'] is None:
            self._kwargs['line_config'] = {
                'train': { 'name': 'Train', 'color': '#F8766D' }
            }
            if do_validation:
                self._kwargs['line_config']['validation'] = \
                    {'name': 'Validation', 'color': '#00BFC4' }

        # set the facet_config, if not specified
        if 'facet_config' not in self._kwargs or self._kwargs['facet_config'] is None:
            self._kwargs['facet_config'] = {}
            for facet_name in self._facet_keys:
                if facet_name == 'loss':
                    self._kwargs['facet_config'][facet_name] = \
                        { 'name': 'loss', 'limit': [0, None] }
                elif facet_name == 'sparse_categorical_accuracy':
                    self._kwargs['facet_config'][facet_name] = \
                        { 'name': 'accuracy', 'limit': [0, 1] }
                else:
                    self._kwargs['facet_config'][facet_name] = \
                        { 'name': facet_name, 'limit': [None, None] }

        # Create plotter
        self._plotter = PlotLearningCurve(**self._kwargs)

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        if self._plotter is None:
            self._setup_plotter(logs.keys())

        # restructure logs data to nested dicts and append
        row = { facet_key: dict() for facet_key in self._facet_keys }
        for metric_name, metric_assigment in self._metric_mapping.items():
            metric_value = float(logs[metric_name]) if metric_name in logs else float('nan')
            row[metric_assigment['facet']][metric_assigment['line']] = metric_value
        self._plotter.append(epoch, row)

        # Update plot
        if epoch % self._draw_interval == 0:
            self._plotter.draw()

    def on_train_end(self, logs=None):
        if self._plotter is not None:
            self._plotter.finalize()
