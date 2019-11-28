window.d3 = Object.assign(
    {},
    // d3.select
    // d3.selectAll
    require('d3-selection'),
    // .transition()
    require('d3-transition'),
    // d3.extent
    require('d3-array'),
    // d3.axisBottom
    // d3.axisLeft
    require('d3-axis'),
    // d3.scaleLinear
    // d3.scaleTime
    require('d3-scale'),
    // d3.line
    require('d3-shape')
);
