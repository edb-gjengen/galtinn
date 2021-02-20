import _ from 'lodash';
import moment from 'moment';
import Chart from 'chart.js';

const chartColors = {
	app: 'rgb(255, 99, 132)',
	cash_register: 'rgb(255, 159, 64)',
	other: 'rgb(255, 205, 86)',
	card: 'rgb(75, 192, 192)',
	sms: 'rgb(54, 162, 235)',
	// purple: 'rgb(153, 102, 255)',
	// grey: 'rgb(201, 203, 207)'
};
const url = '/api/stats/';

let saleTypes = [];
let salesData = {};
let salesDataByDate;

let salesChartEl;
let salesChart;
let salesChartTodayEl;
let salesChartToday;
let salesChartData;


function snakecaseToLabel(text) {
    text = text.replace('_', ' ');
    text = text.charAt(0).toUpperCase() + text.slice(1);
    return text;
}

function toChartJSDatasets(memberships) {
    const dss = _.map(memberships, (series, key) => {
        series = _.sortBy(series, 'date');
        let accumelated = 0;
        let seriesOut = {
            label: snakecaseToLabel(key),
            backgroundColor: chartColors[key]
        };

        seriesOut.data = _.map(series, function (el) {
            accumelated += el.sales;
            return {x: el.date, y: accumelated, sales: el.sales}
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
    const today = moment.utc().format('YYYY-MM-DD');
    $('.today-date-wrap').text(today);

    const todaySales = _.map(salesData, (salesPerDay, key) => {
        return _.find(salesPerDay, {date: today});
    }).filter((el) => { return el !== undefined; });

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

    const salesChartTodayData = _.map(todaySales, (el) => {
        return {
            label: snakecaseToLabel(el.payment_method),
            backgroundColor: chartColors[el.payment_method],
            data: [el.sales]
        }
    });

    if(salesChartToday) {
        salesChartToday.destroy();
    }
    salesChartToday = new Chart(salesChartTodayEl, {
        type: 'pie',
        data: {
            datasets: salesChartTodayData,
            labels: _.map(salesChartTodayData, (el) => { return el.label; })
        },

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

    salesDataByDate = groupSalesByDate();

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
    const csvLines = _.map(data, (day) => {
        return day.date + ',' + _.map(saleTypes, (t) => {
            return day[t] || 0;
        }).join(',');
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

        if (salesChart) {
            salesChart.destroy();
        }
        salesChart = new Chart(salesChartEl, {
            type: 'line',
            data: salesChartData,
            options: {
                tooltips: {
                    callbacks: {
                        label: (tooltipItem, data) => {
                            const dataSet = data.datasets[tooltipItem.datasetIndex];
                            const dataSetItem = dataSet.data[tooltipItem.index];
                            return dataSet.label + ' sales: ' + dataSetItem.sales + ' ' + 'Total: ' + dataSetItem.y;
                        }
                    }
                },
                scales: {
                    yAxes: [{
                        stacked: true,
                    }],
                    xAxes: [{
                        type: 'time',
                    }]
                }
            }
        });

    });
}

$(document).ready(() => {
    const $exportBtn = $('.export-data-btn');
    const $startInput = $('#start');
    salesChartEl = document.getElementById('sales-chart');
    salesChartTodayEl = document.getElementById('sales-chart-today');

    let start = $startInput.val();
    recalc(start);

    /* Dynamic date change */
    $startInput.on('input', (e) => {
        start = $(e.target).val();
        history.replaceState(null, null, '?start_date=' + start);
        recalc(start);
    });

    /* Export to CSV */
    $exportBtn.on('click', (e) => {
        e.preventDefault();
        const fileName = 'medlemskapsstats-' + $startInput.val() + '.csv';
        if( !Object.keys(salesData).length ) {
            return;
        }
        const csvData = toCSV(salesDataByDate);
        downloadCSVFile(csvData, fileName);
    });

});
