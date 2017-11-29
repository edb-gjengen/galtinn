const chartColors = {
	red: 'rgb(255, 99, 132)',
	orange: 'rgb(255, 159, 64)',
	yellow: 'rgb(255, 205, 86)',
	green: 'rgb(75, 192, 192)',
	blue: 'rgb(54, 162, 235)',
	purple: 'rgb(153, 102, 255)',
	grey: 'rgb(201, 203, 207)'
};
const url = '/api/stats/';

let saleTypes = [];
let salesData = {};

let salesChart;
let salesChartToday;
let salesChartData;


function snakecaseToLabel(text) {
    text = text.replace('_', ' ');
    text = text.charAt(0).toUpperCase() + text.slice(1);
    return text;
}

function toChartJSDatasets(memberships) {
    memberships = _.sortBy(memberships, 'date');
    const dss = _.map(memberships, (series, i) => {
        let seriesOut = {
            label: snakecaseToLabel(series[0].payment_method),
            backgroundColor: _.values(chartColors)[i]
        };

        seriesOut.data = _.map(series, function (el) {
            return {x: moment.utc(el.date), y: el.sales}
        });

        return seriesOut;
    });

    return {datasets: dss};
}

function getSales(start, cb) {
    return $.getJSON(url + '?start_date=' + start, function (data) {
        salesData = data.memberships;
        saleTypes = data.payment_methods;
        salesChartData = toChartJSDatasets(salesData);

        if(cb) {
            cb();
        }
    });
}

function totals() {
    let sum = 0;
    _.each(saleTypes, function(type) {
        const total = _.reduce(salesData[type], (memo, num) => { return memo + num.sales; }, 0);
        $('.'+ type).html(total);
        sum += total;
    }) ;

    $('.sum').html(sum);
}

function today() {
    var today = moment.utc().format('YYYY-MM-DD');
    $('.today-date-wrap').text(today);

    const todaySales = _.map(salesData, (salesPerDay, key) => {
        return _.findWhere(salesPerDay, {date: today});
    });

    const sumSales = _.map(todaySales, (x) => {
            if (!x) {
                return 0;
            }
            return x.sales
        })
        .reduce((a, b) => {
            return a + b;
            }, 0);

    $('.sum-today').html(sumSales);


    let salesChartTodayData = salesChartData;
    _.each(salesChartTodayData.datasets, (el) => {
        el.data = _.filter(el.data, (point) => {
            return point.x.format('YYYY-MM-DD') === today;
        })
    });

    new Chart(salesChartToday, {
        type: 'bar',
        data: salesChartTodayData,
        options: {
            scales: {
                yAxes: [{
                    stacked: true,
                    ticks: {
                        stepSize: 1
                    }
                }],
            }
        }
    });
}

function groupSalesByDate() {
    let salesByDate = {};
    _.each(saleTypes, function (type) {
        _.each(salesData[type], function (el) {
            let d = {};
            d[el.date] = {};
            d[el.date][type]= el.sales;

            $.extend(true, salesByDate, d);
        });
    });
    /* add zeros */
    _.each(salesByDate, function (sales, date) {
        _.each(saleTypes, function (type) {
            if(typeof sales[type] == 'undefined') {
                salesByDate[date][type] = 0;
            }
        });
    });

    let tableFriendly = [];
    _.each(salesByDate, function (sales, date) {
        sales.date = date;
        tableFriendly.push(sales);
    });
    tableFriendly = _.sortBy(tableFriendly, 'date').reverse();

    return tableFriendly;
}

function salesTable() {
    // FIXME: translation
    let html = '<thead><tr><th>Dato</th>';
    _.each(saleTypes, function(type) {
        type = snakecaseToLabel(type);
        html += '<th>' + type + '</th>';
    });
    html += '</tr></thead><tbody>';

    const salesDataByDate = groupSalesByDate();

    _.each(salesDataByDate, function(el) {
        html += '<tr><td>' + el.date + '</td>';
        _.each(saleTypes, function(type) {
            html += '<td>' + el[type] + '</td>';
        });
        html += '</tr>';
    });
    html += '</tbody>';

    $('#sales-table').html(html);
}

function toCSV(data) {
    const csvLines = data.map((d) => {
        return d.date + ',' + saleTypes.map(function(t) { return d[t]; }).join(',');
    });
    const csvHeader = 'date,' +saleTypes.join(',') + '\n';
    return csvHeader + csvLines.join('\n')
}

function downloadCSVFile(csvData, fileName) {
    csvData = 'data:text/csv;charset=utf-8,' + csvData;
    const encodedUri = encodeURI(csvData);

    let link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', fileName);
    document.body.appendChild(link); // Required for FF

    link.click();
}

function recalc(start) {
    getSales(start, () => {
        totals();
        salesTable();
        today();

        new Chart(salesChart, {
            type: 'line',
            data: salesChartData,
            options: {
                scales: {
                    yAxes: [{
                        stacked: true,
                    }],
                    xAxes: [{
                        type: 'time',
                        time: {
                            tooltipFormat: 'll'
                        }
                    }]
                }
            }
        });

    });
}

$(document).ready(() => {
    const $exportBtn = $('.export-data-btn');
    const $startInput = $('#start');
    salesChart = document.getElementById('sales-chart');
    salesChartToday = document.getElementById('sales-chart-today');

    const start = $startInput.val();
    recalc(start);

    /* Dynamic date change */
    $startInput.on('input', (e) => {
        history.replaceState(null, null, '?start_date=' + $(e.target).val());
        recalc(start);
    });

    /* Export to CSV */
    $exportBtn.on('click', (e) => {
        e.preventDefault();
        const fileName = 'medlemskapsstats-' + $startInput.val() + '.csv';
        const csvData = toCSV(salesData);
        downloadCSVFile(csvData, fileName);
    });

});
