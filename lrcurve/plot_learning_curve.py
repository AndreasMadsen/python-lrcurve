
import uuid
import json
import os.path as path
import IPython

web_assets_dir = path.join(path.dirname(path.realpath(__file__)), 'web_assets')

def _valid_limit(limit):
    return (
        isinstance(limit, list) and
        len(limit) == 2 and
        (limit[0] is None or isinstance(limit[0], (float, int))) and
        (limit[1] is None or isinstance(limit[1], (float, int)))
    )

class PlotLearningCurve:
    """Framework agnostic interface to plot learning curves.

    This is useful for PyTorch or pure TensorFlow. You should properly use
    `KerasLearningCurve` if you use keras.

    Line description: dict with the properties `name` and `color`.
    Axis description:

    Example:
        plot = PlotLearningCurve()
        for epoch in range(100):
            plot.append(epoch, {
                'loss': {
                    'train': compute_loss(train_x, train_y),
                    'validation': compute_loss(valid_x, valid_y)
                }
            })
            plot.draw()
        plot.finalize()

    Arguments:
        height: The height in pixels of the plot (default None). The default
            behavior is to use 200px per facet and an additional 90px for
            the x-axis and legend.
        width: The width in pixels of the plot (default 600).
        line_config: dict mapping line-keywords to presented name and color.
            The name is a string and the color should be CSS-SVG compatible.
            Default is:
                {
                    'train': { 'name': 'Train', 'color': '#F8766D' },
                    'validation': { 'name': 'Validation', 'color': '#00BFC4' }
                }
        facet_config: dict mapping facet-keyword to presented name and y-axis
            limits. The name is a string, and the limit is an array `[ymin, ymax]`.
            The `ymin` or `ymax` can be set to `None`, which causes the plot to
            dynamically change.
            Default is:
                {
                    'loss': { 'name': 'loss', 'limit': [0, None] }
                }
        xaxis_config: dict describing the presented name and x-axis limit. The name
            is a string, and the limit is an array `[xmin, xmax]`.
            The `xmin` or `xmax` can be set to `None`, which causes the plot to
            dynamically change.
            Default is:
                { 'name': 'Epoch', 'limit': [0, None] }
        display_fn: To display HTML or JavaScript in a notebook with an IPython
            backend, `IPython.display.display` is called. The called function
            can be overwritten by setting this argument (mostly useful for
            internal testing).
        debug: Depending on the notebook, a JavaScript evaluation does not provide
            a stack trace in the developer console. Setting this to `true` works
            around that by injecting `<script>` tags instead.
    """
    def __init__(self,
                 height = None,
                 width = 600,
                 line_config = {
                     'train': { 'name': 'Train', 'color': '#F8766D' },
                     'validation': { 'name': 'Validation', 'color': '#00BFC4' }
                 },
                 facet_config = {
                     'loss': { 'name': 'loss', 'limit': [0, None] }
                 },
                 xaxis_config = { 'name': 'Epoch', 'limit': [0, None] },
                 display_fn=IPython.display.display,
                 debug=False
    ):
        height = len(facet_config) * 200 + 90 if height is None else height

        # arguments assertion
        if not isinstance(height, int) or height <= 0:
            raise ValueError(f'height must be a positive number or None, was {height}')

        if not isinstance(width, int) or width <= 0:
            raise ValueError(f'width must be a positive number, was {width}')

        if not isinstance(line_config, dict):
            raise ValueError('line_config must be a dict')
        for line_key, line_description in line_config.items():
            if 'name' not in line_description or not isinstance(line_description['name'], str):
                raise ValueError(f'line_config["{line_key}"]["name"] must a string')
            if 'color' not in line_description or not isinstance(line_description['color'], str):
                raise ValueError(f'line_config["{line_key}"]["color"] must a string')

        if not isinstance(facet_config, dict):
            raise ValueError('line_config must be a dict')
        for facet_key, facet_description in facet_config.items():
            if 'name' not in facet_description or not isinstance(facet_description['name'], str):
                raise ValueError(f'facet_config["{facet_key}"]["name"] must a string')
            if 'limit' not in facet_description or not _valid_limit(facet_description['limit']):
                raise ValueError(f'facet_config["{facet_key}"]["limit"] must be a list with length two')

        if 'name' not in xaxis_config or not isinstance(xaxis_config['name'], str):
            raise ValueError(f'xaxis_config["name"] must a string')
        if 'limit' not in xaxis_config or not _valid_limit(xaxis_config['limit']):
            raise ValueError(f'xaxis_config["limit"] must be a list with length two')

        # Store settings
        self._debug = debug
        self._display = display_fn
        self._settings = {
            'id': str(uuid.uuid4()),
            'width': width,
            'height': height,
            'lineConfig': line_config,
            'facetConfig': facet_config,
            'xAxisConfig': xaxis_config
        }

        # Prepear data containers
        self._data = []
        self._backlog = []
        self._display(self._create_inital_html())
        self._update_element = self._display(
            IPython.display.Javascript('void(0);'),
            display_id=True
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.finalize()

    def _create_inital_html(self):
        with open(path.join(web_assets_dir, 'd3.bundle.js')) as d3_fp, \
             open(path.join(web_assets_dir, 'learning_curve.css')) as css_fp, \
             open(path.join(web_assets_dir, 'learning_curve.js')) as js_fp:
            return IPython.display.HTML(
                f'<style>{css_fp.read()}</style>'
                f'<script>{d3_fp.read()}</script>'
                f'<script>{js_fp.read()}</script>'
                f'<svg id="{self._settings["id"]}" class="learning-curve"></svg>'
                f'<script>'
                f'  window.setupLearningCurve({json.dumps(self._settings)});'
                f'</script>'
            )

    def _create_append_javascript(self):
        if self._debug:
            return IPython.display.HTML(
                f'<script>'
                f'  window.appendLearningCurve({json.dumps(self._backlog)});'
                f'</script>'
            )
        else:
            return IPython.display.Javascript(
                f'window.appendLearningCurve({json.dumps(self._backlog)});'
            )

    def append(self, x, y):
        """Appends graph data without updateing the figure.

        It can be useful to append several data-points before updateing the
        figure with `.draw()`.

        Arguments:
            x: number - The x axis value, typically the epoch or iteration.
            y: dict - The measured values for this epoch, structured as a
                dict mapping from facet-keywords to a nested dict. The
                nested dict maps from line-keyword to measured value.
        """
        row = {
            'x': float(x),
            'y': {
                facet_key: {
                    line_key: float(value) for line_key, value in facet_data.items()
                } for facet_key, facet_data in y.items()
            }
        }
        self._data.append(row)
        self._backlog.append(row)

    def draw(self):
        """Updates the figure with the appended data.

        Remember to call `.finalize()` to make the new figure presist in
        the saved notebook.
        """
        if len(self._backlog) > 0:
            disp = self._create_append_javascript()
            self._backlog = []
            self._update_element.update(disp)

    def finalize(self):
        """Saves the data to the notebook file, such the graph is presistent.

        If this function is not called the graph will appear empty next time
        the notebook file is opened. If saving the notebook results is not
        required, then calling this method is optional.
        """
        # In case there is data left in the backlog, draw it
        if len(self._backlog) > 0:
            self.draw()

        # Add a <script> tag containing the data, without affecting the current
        # figure.
        if self._update_element is not None:
            self._update_element.update(
                IPython.display.Javascript(
                    'window.appendLearningCurve = function () {};'
                )
            )
            self._update_element.update(
                IPython.display.HTML(
                    f'<script>'
                    f'  window.appendLearningCurve({json.dumps(self._data)});'
                    f'</script>'
                )
            )
