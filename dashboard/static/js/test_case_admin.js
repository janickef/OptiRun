$(document).ready(function() {
    $(".result-dist").sparkline('html', {
        type: 'bar',
        barWidth: 20,
        chartRangeMin: 1,
        tooltipFormat: '<span style="color:{{color}}">&#9679;</span> {{offset:names}}: {{value}}',
        tooltipValueLookups: {
            names: {
                0: 'Passed',
                1: 'Failed',
                2: 'Not Executed',
            }
        },
        colorMap: ['#79aec8','#333','#999'],
    });
});