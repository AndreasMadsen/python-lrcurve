;(function () {
  'use strict';
  const d3 = window.d3;

  const margin = {top: 10, right: 10, bottom: 10, left: 45};
  const axisMargin = { top: 10, right: 15, bottom: 10, left: 15 };
  const facetWidth = 30;
  const legendHeight = 40;
  const xAxisHeight = 30;
  const xLabelHeight = 20;

  function unique(items) {
    return Array.from(new Set(items));
  }

  function nonFiniteDefaultNull(number) {
    return Number.isFinite(number) ? number : null;
  }

  function computeLimit(original, data, lineKeys, fn) {
    let min = Infinity;
    let max = -Infinity;

    for (const lineKey of lineKeys) {
      const storage = data.get(lineKey);
      if (storage.length > 0) {
        const [localMin, localMax] = d3.extent(storage.map(fn));
        min = Math.min(min, localMin);
        max = Math.max(max, localMax);
      }
    }

    return [
      original[0] === null ? nonFiniteDefaultNull(min) : original[0],
      original[1] === null ? nonFiniteDefaultNull(max) : original[1]
    ];
  }

  function highestMinorMod(majorTickCount, minorTickMax) {
    return Math.floor((minorTickMax - 1) / (majorTickCount - 1));
  }

  function createGridTicks(majorTicks, minorMod) {
    const minorTicks = [];
    for (let majorIndex = 0; majorIndex < majorTicks.length - 1; majorIndex++) {
      minorTicks.push(majorTicks[majorIndex]);
      const distance = majorTicks[majorIndex + 1] - majorTicks[majorIndex];
      for (let i = 1; i <= minorMod - 1; i++) {
        minorTicks.push(majorTicks[majorIndex] + (i / minorMod) * distance);
      }
    }
    minorTicks.push(majorTicks[majorTicks.length - 1]);
    return minorTicks;
  }

  class SubGraph {
    constructor({ container, id, index, height, width, drawXAxis, lineKeys, lineConfig, facetLabel, yscale, ylim, xlim }) {
      this.container = container;

      this.graphWidth = width - facetWidth - margin.left - margin.right;
      this.graphHeight = height - margin.top - margin.bottom;

      this.axisWidth = this.graphWidth - axisMargin.left - axisMargin.right;
      this.axisHeight = this.graphHeight - axisMargin.top - axisMargin.bottom;

      this.xlim = xlim;
      this.dynamicXlim = this.xlim.includes(null);
      this.ylim = ylim;
      this.dynamicYlim = this.ylim.includes(null);

      this.lineKeys = lineKeys;
      this.lineConfig = lineConfig;

      // Create graph container
      this.graph = this.container.append('g')
        .attr('transform',
              'translate(' + margin.left + ',' + margin.top + ')');

      // Create facet
      this.facet = this.container.append('g')
        .classed('facet', true)
        .attr('transform', `translate(${margin.left + this.graphWidth}, ${margin.top})`);
      this.facet.append('rect')
        .classed('facet-background', true)
        .attr('width', facetWidth)
        .attr('height', this.graphHeight);
      const facetTextPath = this.facet.append('path')
        .attr('d', `M10,0 V${this.graphHeight}`)
        .attr('id', `learning-curve-${id}-${index}-facet-text`);
      const facetText = this.facet.append('text')
        .append('textPath')
        .attr('startOffset', '50%')
        .attr('href', `#learning-curve-${id}-${index}-facet-text`)
        .attr('text-anchor', 'middle')
        .text(facetLabel);
      facetText.node()
        .setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `#learning-curve-${id}-${index}-facet-text`);

      // Create background
      this.background = this.graph.append("rect")
        .attr("class", "background")
        .attr("height", this.graphHeight)
        .attr("width", this.graphWidth);

      // define scales
      this.xScale = d3.scaleLinear()
        .range([0, this.axisWidth]);

      this.yScale = (yscale === 'log10' ? d3.scaleLog() : d3.scaleLinear())
        .range([this.axisHeight, 0]);

      // compute tick marks
      this._updateXscale(this.xlim);
      this._updateYscale(this.ylim);

      // create x-grid
      this.xGrid = d3.axisBottom(this.xScale)
        .tickValues(this.xTicksGrid)
        .tickSize(-this.graphHeight);
      this.xGridElement = this.graph.append("g")
          .attr("class", "grid")
          .attr("transform", `translate(${axisMargin.left},${this.graphHeight})`);

      // create y-grid
      this.yGrid = d3.axisLeft(this.yScale)
        .tickValues(this.yTicksGrid)
        .tickSize(-this.graphWidth);
      this.yGridElement = this.graph.append("g")
          .attr("class", "grid")
          .attr('transform', `translate(0,${axisMargin.top})`);

      // define x-axis
      this.xAxis = d3.axisBottom(this.xScale)
        .tickValues(this.xTicks);
      this.xAxisElement = this.graph.append('g')
        .attr("class", "axis")
        .classed('hide-axis', !drawXAxis)
        .attr('transform', `translate(${axisMargin.left},${this.graphHeight})`);

      // define y-axis
      this.yAxis = d3.axisLeft(this.yScale)
        .tickValues(this.yTicks);
      this.yAxisElement = this.graph.append('g')
        .attr("class", "axis")
        .attr('transform', `translate(0,${axisMargin.top})`);

      // draw axis
      if (!this.dynamicYlim) this._drawYaxis();
      if (!this.dynamicXlim) this._drawXaxis();

      // Define drawer functions and line elements
      this.lineDrawers = new Map();
      this.lineElements = new Map();
      const self = this;
      for (const lineKey of this.lineKeys) {
        // create drawer function
        const lineDrawer = d3.line()
            .x((d) => self.xScale(d.x))
            .y((d) => this.yScale(d.y));
        this.lineDrawers.set(lineKey, lineDrawer);

        // create line element
        const lineElement = this.graph.append('path')
            .attr('class', 'line')
            .attr('transform', `translate(${axisMargin.left},${axisMargin.top})`)
            .attr('stroke', lineConfig[lineKey].color);
        this.lineElements.set(lineKey, lineElement);
      }
    }

    _updateXscale(xlim) {
      this.xScale.domain(xlim).nice(6);
      this.xTicks = this.xScale.ticks(6);
      this.xTicksMod = highestMinorMod(this.xTicks.length, 19);
      this.xTicksGrid = createGridTicks(this.xTicks, this.xTicksMod);
    }

    _drawXaxis() {
      // update x-grid
      this.xGridElement.transition()
        .call(this.xGrid.tickValues(this.xTicksGrid))
        .call((transition) => transition
          .selectAll('.tick')
          .style('stroke-opacity', (v) => this.xTicks.includes(v) ? '1.0' : '0.5')
        );

      // update x-axis
      this.xAxisElement.transition().call(
        this.xAxis.tickValues(this.xTicks)
      );
    }

    _updateYscale(ylim) {
      this.yScale.domain(ylim).nice(3);
      this.yTicks = this.yScale.ticks(3);
      this.yTicksMod = highestMinorMod(this.yTicks.length, 9);
      this.yTicksGrid = createGridTicks(this.yTicks, this.yTicksMod);
    }

    _drawYaxis() {
      // update x-grid
      this.yGridElement.transition()
        .call(this.yGrid.tickValues(this.yTicksGrid))
        .call((transition) => transition
          .selectAll('.tick')
          .style('stroke-opacity', (v) => this.yTicks.includes(v) ? '1.0' : '0.5')
        );
      // update x-axis
      this.yAxisElement.transition().call(
        this.yAxis.tickValues(this.yTicks)
      );
    }

    setData (data) {
      // Compute x-axis limit
      if (this.dynamicXlim) {
        const xlim = computeLimit(this.xlim, data, this.lineKeys, (d) => d.x);
        if (xlim[0] !== this.xlim[0] || xlim[1] !== this.xlim[1]) {
          this._updateXscale(xlim);
        }
      }

      // Update y-axis limit
      if (this.dynamicYlim) {
        const ylim = computeLimit(this.ylim, data, this.lineKeys, (d) => d.y);
        if (ylim[0] !== this.ylim[0] || ylim[1] !== this.ylim[1]) {
          this._updateYscale(ylim);
        }
      }

      // Update line data
      for (let lineKey of this.lineKeys) {
        this.lineElements.get(lineKey).data([
          data.get(lineKey)
        ]);
      }
    }

    draw() {
      if (this.dynamicXlim) this._drawXaxis();
      if (this.dynamicYlim) this._drawYaxis();

      // update lines
      for (let lineKey of this.lineKeys) {
        this.lineElements.get(lineKey)
          .attr('d', this.lineDrawers.get(lineKey));
      }
    }
  }

  class LearningCurvePlot {
    constructor({ id, height, width, mappings, facetConfig, lineConfig, xAxisConfig }) {
      this.facetKeys = unique(Object.values(mappings).map(({line, facet}) => facet)).sort();

      const innerHeight = height - legendHeight - xLabelHeight - xAxisHeight;
      const subGraphHeight = innerHeight / this.facetKeys.length;

      this._container = d3.select(document.getElementById(id))
      .classed('learning-curve', true)
      .style('height', `${height}px`)
      .style('width', `${width}px`)
      .attr('height', height)
      .attr('width', width)
      .attr('xmlns:xlink', 'http://www.w3.org/1999/xlink');

      // Create a SubGraph for each facet
      this._facets = new Map();
      for (let facetIndex = 0; facetIndex < this.facetKeys.length; facetIndex++) {
        const facetKey = this.facetKeys[facetIndex];
        const lineKeys = unique(
            Object.values(mappings)
            .filter(({facet, line}) => facet === facetKey)
            .map(({facet, line}) => line)
        ).sort();
        this._facets.set(
          facetKey,
          new SubGraph({
            container: this._container.append('g')
              .attr('transform', `translate(0, ${facetIndex * subGraphHeight})`),
            id: id,
            index: facetIndex,
            height: Math.round(subGraphHeight),
            width: width,

            drawXAxis: facetIndex == this.facetKeys.length - 1,

            lineKeys: lineKeys,
            lineConfig: lineConfig,
            facetLabel: facetConfig[facetKey].name,
            yscale: facetConfig[facetKey].scale,
            ylim: facetConfig[facetKey].limit,
            xlim: xAxisConfig.limit
          })
        );
      }

      const afterSubGraphHeight = height - legendHeight - xLabelHeight;
      const plotWidth = width - margin.left - margin.right;
      const xAxisWidth = plotWidth - facetWidth;

      // Draw x-axis label
      this._xLabel = this._container.append('text')
        .attr('text-anchor', 'middle')
        .attr('transform', `translate(${margin.left}, ${afterSubGraphHeight})`)
        .attr('x', xAxisWidth / 2)
        .text(xAxisConfig.name);

      // Draw legends
      this._legend = this._container
        .append('g')
        .classed('legned', true)
        .attr('transform', `translate(${margin.left}, ${afterSubGraphHeight + xLabelHeight})`);
      this._legendOfsset = this._legend.append('g');

      let currentOffset = 0;
      for (const {name, color} of Object.values(lineConfig)) {
        // Draw rect with line inside [-]
        this._legendOfsset.append('rect')
          .attr('width', 25)
          .attr('height', 25)
          .attr('x', currentOffset);
        this._legendOfsset.append('line')
          .attr('x1', currentOffset + 2)
          .attr('x2', currentOffset + 25 - 2)
          .attr('y1', 25/2)
          .attr('y2', 25/2)
          .attr('stroke', color);
        currentOffset += 30;

        // Draw text
        const textNode = this._legendOfsset.append('text')
          .attr('x', currentOffset)
          .attr('y', 19)
          .text(name);
        const textWidth = textNode.node().getComputedTextLength();
        currentOffset += textWidth + 20;
      }
      currentOffset -= 20;

      this._legendOfsset
        .attr('transform', `translate(${(plotWidth - currentOffset) / 2}, 0)`);
    }

    setData(data) {
      for (let facetKey of this.facetKeys) {
        this._facets.get(facetKey).setData(data.get(facetKey));
      }
    }

    draw() {
      for (let facetKey of this.facetKeys) {
        this._facets.get(facetKey).draw();
      }
    }

    remove() {
      this._container.selectAll("*").remove();
    }
  }

  // Class to accumulate and store all data
  class LearningCurveData {
    constructor(settings) {
      this.index = new Map();
      this.data = new Map();
      this.updateSettings(settings);
    }

    updateSettings (settings) {
      for (const [key, {line, facet}] of Object.entries(settings.mappings)) {
        if (this.data.has(key)) {
          continue;
        }

        if (!this.index.has(facet)) {
          this.index.set(facet, new Map());
        }
        if (!this.index.get(facet).has(line)) {
          const storage = [];
          this.index.get(facet).set(line, storage);
          this.data.set(key, storage);
        }
      }
    }

    append([x, y]) {
      for (const [key, storage] of this.data.entries()) {
        if (Object.prototype.hasOwnProperty.call(y, key)) {
          storage.push({
            x: x,
            y: y[key]
          })
        }
      }
    }

    appendAll(rows) {
      for (const row of rows) {
        this.append(row);
      }
    }

    get(facet) {
      return this.index.get(facet);
    }
  }

  class LearningCurveDrawScheduler {
    constructor(settings) {
      this.waitingForDrawing = false;
      this.graph = new LearningCurvePlot(settings);
      this.data = new LearningCurveData(settings);
    }

    updateSettings(settings) {
      this.graph.remove();
      this.graph = new LearningCurvePlot(settings);
      this.data.updateSettings(settings);
      this.draw();
    }

    draw() {
      this.waitingForDrawing = false;
      this.graph.setData(this.data);
      this.graph.draw();
    }

    appendAllAndUpdate(data) {
      this.data.appendAll(data);

      if (!this.waitingForDrawing) {
        this.waitingForDrawing = true;
        window.requestAnimationFrame(this.draw.bind(this));
      }
    }
  }

  window.setupLearningCurve = function (id, settings) {
    if (document.getElementById(id).instance) {
      document.getElementById(id).instance.updateSettings(settings);
    } else {
      document.getElementById(id).instance = new LearningCurveDrawScheduler(settings);
    }
  };

  window.appendLearningCurve = function (id, data) {
    document.getElementById(id).instance.appendAllAndUpdate(data);
  };
})();
