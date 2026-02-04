import React, { useEffect, useState } from 'react';
import { BarChart } from '@mui/x-charts/BarChart';
import { LineChart } from '@mui/x-charts/LineChart';
import { PieChart } from '@mui/x-charts/PieChart';
import { useDrawingArea } from '@mui/x-charts/hooks';
import { styled } from '@mui/material/styles';
import { TrendingDown, AlertTriangle, ArrowDownRight, Trophy, Map } from 'lucide-react';
import Chart from 'react-apexcharts';

// Modern Light Theme Palette (Rose)
const COLORS = ['#F43F5E', '#E11D48', '#BE123C', '#9F1239', '#881337'];

const getMetricKey = (data) => {
    if (!data || data.length === 0) return 'total_sales';
    const keys = Object.keys(data[0]);
    const found = keys.find(k => ['sales', 'total_sales', 'profit', 'amount', 'quantity', 'value', 'impact', 'sales_change'].includes(k.toLowerCase()));
    return found || keys.find(k => typeof data[0][k] === 'number') || 'total_sales';
};

const getLabelKey = (data) => {
    if (!data || data.length === 0) return 'month';
    const keys = Object.keys(data[0]);
    // Known dimension keys to look for first (including common TYPO handling)
    const priority = ['month', 'year', 'quarter', 'date', 'order_date', 'category', 'sub-category', 'sub_category', 'sub_categoory', 'region', 'product_name', 'segment', 'state', 'city'];
    const foundPriority = priority.find(p => keys.includes(p));
    if (foundPriority) return foundPriority;

    const invalid = ['sales', 'total_sales', 'profit', 'amount', 'quantity', 'value', 'count', 'impact', 'cost', 'discount', 'sales_change'];
    const found = keys.find(k => !invalid.includes(k.toLowerCase()) && typeof data[0][k] === 'string');
    return found || 'month';
};

const getCommonOptions = (theme = 'light') => ({
    chart: {
        background: 'transparent',
        toolbar: { show: false },
        animations: { enabled: true },
        fontFamily: 'Inter, sans-serif'
    },
    theme: { mode: 'light' },
    dataLabels: { enabled: false },
    grid: { show: false, borderColor: '#E5E7EB' }, // Gray-200
    xaxis: {
        labels: { style: { colors: '#374151' } }, // Gray-700
        axisBorder: { show: false },
        axisTicks: { show: false }
    },
    yaxis: {
        labels: { style: { colors: '#374151' } }
    },
    legend: { labels: { colors: '#374151' } },
    tooltip: { theme: 'light' }
});

const getBoxPlotConfig = (data, metricKey, labelKey) => {
    const series = [{
        type: 'boxPlot',
        data: data.map(d => ({
            x: d[labelKey],
            y: d.quartiles || [d[metricKey] * 0.8, d[metricKey] * 0.9, d[metricKey], d[metricKey] * 1.1, d[metricKey] * 1.2]
        }))
    }];

    return {
        series,
        options: {
            ...getCommonOptions(),
            chart: { type: 'boxPlot', height: 350 },
            title: { text: `Distribution of ${metricKey}`, align: 'left', style: { color: '#F43F5E' } },
            plotOptions: {
                boxPlot: {
                    colors: {
                        upper: '#F43F5E',
                        lower: '#BE123C'
                    }
                }
            }
        }
    };
};

const getHeatmapConfig = (data, metricKey, labelKey) => {
    const series = [{
        name: metricKey,
        data: data.map(d => ({
            x: d[labelKey],
            y: d[metricKey]
        }))
    }];

    return {
        series,
        options: {
            ...getCommonOptions(),
            chart: { type: 'heatmap', height: 350 },
            plotOptions: {
                heatmap: {
                    shadeIntensity: 0.5,
                    radius: 0,
                    useFillColorAsStroke: true,
                    colorScale: {
                        ranges: [{
                            from: 0,
                            to: 1000000000,
                            name: 'scale',
                            color: '#F43F5E'
                        }]
                    }
                }
            },
            dataLabels: { enabled: false },
            stroke: { width: 1, colors: ['#fff'] }
        }
    };
}

const getTreemapConfig = (data, metricKey, labelKey) => ({
    series: [{
        data: data.map(d => ({
            x: d[labelKey],
            y: d[metricKey]
        }))
    }],
    options: {
        ...getCommonOptions(),
        chart: { type: 'treemap', height: 350 },
        colors: ['#F43F5E', '#FB7185', '#FDA4AF', '#BE123C'],
        title: { text: `Composition by ${labelKey}`, style: { color: '#F43F5E' } }
    }
});

const getBubbleConfig = (data, metricKey, labelKey) => {
    const series = [{
        name: metricKey,
        data: data.map((d, i) => ([
            i + 10,
            d[metricKey],
            d[metricKey] / 100
        ]))
    }];

    return {
        series,
        options: {
            ...getCommonOptions(),
            chart: { type: 'bubble', height: 350 },
            xaxis: { type: 'numeric', labels: { style: { colors: '#374151' } } },
            fill: { opacity: 0.8 },
            colors: ['#F43F5E']
        }
    };
}

const getAreaChartConfig = (data, metricKey, labelKey) => ({
    series: [{
        name: metricKey,
        data: data.map(d => d[metricKey])
    }],
    options: {
        ...getCommonOptions(),
        chart: { type: 'area', height: 350 },
        stroke: { curve: 'smooth', colors: ['#F43F5E'] },
        xaxis: { categories: data.map(d => d[labelKey]), labels: { style: { colors: '#374151' } } },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.3,
                stops: [0, 90, 100],
                colorStops: [
                    { offset: 0, color: "#F43F5E", opacity: 0.8 },
                    { offset: 100, color: "#BE123C", opacity: 0.2 }
                ]
            }
        },
        dataLabels: { enabled: false }
    }
});


export function AnalysisSection({ type, title, data, loading }) {
    if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-xl" />

    // Safety check for error object or invalid data
    if (!data) return null;
    if (data.error) {
        return (
            <div className="bg-red-50 p-4 rounded-xl border border-red-100 my-4">
                <h3 className="text-red-500 font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle size={16} />
                    Analysis Error
                </h3>
                <code className="text-xs text-red-400 block overflow-auto whitespace-pre-wrap">
                    {data.error}
                </code>
            </div>
        )
    }
    if (!Array.isArray(data) || data.length === 0) return null;

    const metricKey = getMetricKey(data)
    const labelKey = getLabelKey(data)

    const normalizedData = data.map(item => {
        const newItem = { ...item };
        // Ensure metric is a number (handle null/undefined)
        if (newItem[metricKey] == null) newItem[metricKey] = 0;
        // Ensure label is a string
        if (newItem[labelKey] == null) newItem[labelKey] = 'Unknown';
        return newItem;
    });

    const isHorizontal = type === 'region' || type === 'rca' || type === 'decline' || type === 'bar';
    const chartHeight = isHorizontal ? Math.max(400, normalizedData.length * 50) : 400;

    const commonProps = {
        dataset: normalizedData,
        margin: { top: 20, bottom: 40, left: 100, right: 20 },
        height: chartHeight,
        slotProps: { legend: { hidden: true } }
    }

    // --- Chart Selection Logic ---
    let ChartComponent = null;

    // Advanced Charts (ApexCharts)
    if (['box_plot', 'box', 'violin'].includes(type)) {
        const config = getBoxPlotConfig(normalizedData, metricKey, labelKey);
        ChartComponent = <Chart options={config.options} series={config.series} type="boxPlot" height={350} />;
    } else if (['heatmap'].includes(type)) {
        const config = getHeatmapConfig(normalizedData, metricKey, labelKey);
        ChartComponent = <Chart options={config.options} series={config.series} type="heatmap" height={350} />;
    } else if (['treemap'].includes(type)) {
        const config = getTreemapConfig(normalizedData, metricKey, labelKey);
        ChartComponent = <Chart options={config.options} series={config.series} type="treemap" height={350} />;
    } else if (['bubble'].includes(type)) {
        const config = getBubbleConfig(normalizedData, metricKey, labelKey);
        ChartComponent = <Chart options={config.options} series={config.series} type="bubble" height={350} />;
    } else if (['area'].includes(type)) { // Explicit area chart request
        const config = getAreaChartConfig(normalizedData, metricKey, labelKey);
        ChartComponent = <Chart options={config.options} series={config.series} type="area" height={350} />;
    }

    // Standard Charts (MUI) or Fallbacks
    else if (type === 'aggregate' && normalizedData.length === 1) {
        ChartComponent = (
            <div className="flex flex-col items-center justify-center h-[300px] text-center">
                <span className="text-gray-500 text-lg mb-2 capitalize">{metricKey.replace(/_/g, ' ')}</span>
                <span className="text-6xl font-bold text-gray-900 tracking-tight">
                    {normalizedData[0][metricKey]?.toLocaleString('en-US', { style: 'decimal', maximumFractionDigits: 2 })}
                </span>
                <span className="text-rose-500 text-sm mt-3 font-medium bg-rose-50 px-3 py-1 rounded-full">
                    Aggregate Value
                </span>
            </div>
        );
    } else if (['trend', 'line', 'scatter', 'lag'].includes(type)) {
        const isScatter = type === 'scatter' || type === 'lag';
        ChartComponent = (
            <LineChart
                {...commonProps}
                xAxis={[{
                    scaleType: 'point',
                    dataKey: labelKey,
                    tickLabelStyle: { fill: '#374151', fontSize: 12 },
                    labelStyle: { fill: '#374151' }
                }]}
                yAxis={[{
                    labelStyle: { fill: '#374151' },
                    tickLabelStyle: { fill: '#374151', fontSize: 12 }
                }]}
                series={[
                    {
                        dataKey: metricKey,
                        area: !isScatter, // Area for line/trend, not for scatter
                        color: isScatter ? '#FB7185' : '#F43F5E', // Rose
                        showMark: isScatter,
                        showLine: !isScatter,
                    }
                ]}
                grid={{ vertical: isScatter, horizontal: true }}
                sx={{
                    '.MuiChartsAxis-line': { stroke: '#E5E7EB' },
                    '.MuiChartsAxis-tick': { stroke: '#E5E7EB' },
                }}
            />
        );
    } else if (['distribution', 'pie', 'donut'].includes(type)) {
        const isDonut = type === 'donut';
        ChartComponent = (
            <PieChart
                series={[
                    {
                        data: normalizedData.map((d, i) => ({
                            id: i,
                            value: Math.abs(d[metricKey]),
                            label: d[labelKey],
                            color: COLORS[i % COLORS.length]
                        })),
                        innerRadius: isDonut ? 70 : 30,
                        outerRadius: 100,
                        paddingAngle: 5,
                        cornerRadius: 5,
                        highlightScope: { faded: 'global', highlighted: 'item' },
                        faded: { innerRadius: 30, additionalRadius: -30, color: 'gray' },
                    },
                ]}
                height={300}
                slotProps={{
                    legend: {
                        direction: 'column',
                        position: { vertical: 'middle', horizontal: 'end' },
                    }
                }}
                sx={{
                    '.MuiChartsLegend-series text': { fill: '#374151 !important' },
                    '.MuiChartsLegend-root text': { fill: '#374151 !important' },
                    '.MuiChartsLegend-label': { fill: '#374151 !important' },
                    '.MuiChartsLabel-root': { fill: '#374151 !important' },
                    '.MuiChartsLegend-root': { fill: '#374151 !important', color: '#374151 !important' },
                }}
            />
        );
    } else {
        // Default to Bar for 'region', 'products', 'bar', 'lollipop', 'stacked', 'decline', 'rca'
        ChartComponent = (
            <BarChart
                {...commonProps}
                layout={isHorizontal ? 'horizontal' : 'vertical'}
                xAxis={isHorizontal ?
                    [{ tickLabelStyle: { fill: '#374151', fontSize: 12 } }] :
                    [{ scaleType: 'band', dataKey: labelKey, tickLabelStyle: { fill: '#374151', fontSize: 12 } }]
                }
                yAxis={isHorizontal ?
                    [{
                        scaleType: 'band',
                        dataKey: labelKey,
                        tickLabelStyle: { fill: '#374151', fontSize: 12 },
                        valueFormatter: (value) => value
                    }] :
                    [{ tickLabelStyle: { fill: '#374151', fontSize: 12 } }]
                }
                series={[{ dataKey: metricKey, color: '#F43F5E' }]}
                sx={{
                    '.MuiChartsAxis-line': { stroke: '#E5E7EB' },
                    '.MuiChartsAxis-tick': { stroke: '#E5E7EB' },
                }}
            />
        );
    }

    return (
        <div style={{ width: '100%' }}>
            <h3 className="text-gray-800 font-semibold mb-4 text-sm uppercase tracking-wider flex items-center gap-2 font-outfit">
                <span className="w-2 h-2 bg-rose-500 rounded-full shadow-sm"></span>
                <span className="tracking-widest">{title || "Data Analysis"}</span>
            </h3>

            <div style={{ width: '100%', height: chartHeight }}>
                {ChartComponent}
            </div>
        </div>
    )
}

export default AnalysisSection;
