$(document).ready(function() {
    $(".result-dist").sparkline('html', {
        type: 'bar',
        barWidth: 20,
        chartRangeMin: 1,
        // tooltipFormat: '<span style="color: {{color}}">&#9679;</span> {{offset:names}} ({{value}} - {{percent.1}}%)',
        tooltipFormat: '<span style="color:{{color}}">&#9679;</span> {{offset:names}}: {{value}}',
        tooltipValueLookups: {
            names: {
                0: 'Passed',
                1: 'Failed',
                2: 'Not Executed',
            }
        },
        // colorMap: ['#70BF2B','#E46B6B','#999'],
        colorMap: ['#79aec8','#333','#999'],
    });
});

/*
$(document).ready(function() {
    $("#changelist").append('<div id="chartContainer" style="height: 300px; width: 100%;"></div>');

    var options = {
		title: {
			text: "Spline Chart using jQuery Plugin"
		},
                animationEnabled: true,
		data: [
		{
			type: "spline", //change it to line, area, column, pie, etc
			dataPoints: [
				{ x: 10, y: 10 },
				{ x: 20, y: 12 },
				{ x: 30, y: 8 },
				{ x: 40, y: 14 },
				{ x: 50, y: 6 },
				{ x: 60, y: 24 },
				{ x: 70, y: -4 },
				{ x: 80, y: 10 }
			]
		}
		]
	};

	$("#chartContainer").CanvasJSChart(options);
});
*/