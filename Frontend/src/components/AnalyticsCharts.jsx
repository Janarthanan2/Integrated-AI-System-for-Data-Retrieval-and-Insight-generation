import React, { useEffect, useState } from 'react';
import { BarChart } from '@mui/x-charts/BarChart';
import { LineChart } from '@mui/x-charts/LineChart';
import { PieChart } from '@mui/x-charts/PieChart';
import { useDrawingArea } from '@mui/x-charts/hooks';
import { styled } from '@mui/material/styles';
import { TrendingDown, AlertTriangle, ArrowDownRight, Trophy, Map } from 'lucide-react';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#10b981'];

const getMetricKey = (data) => {
    if (!data || data.length === 0) return 'total_sales';
    const keys = Object.keys(data[0]);
    const found = keys.find(k => ['sales', 'total_sales', 'profit', 'amount', 'quantity', 'value', 'impact'].includes(k.toLowerCase()));
    return found || keys.find(k => typeof data[0][k] === 'number') || 'total_sales';
};

const getLabelKey = (data) => {
    if (!data || data.length === 0) return 'month';
    const keys = Object.keys(data[0]);
    // Known dimension keys to look for first
    const priority = ['month', 'year', 'date', 'order_date', 'category', 'sub_category', 'region', 'product_name', 'segment', 'state', 'city'];
    const foundPriority = priority.find(p => keys.includes(p));
    if (foundPriority) return foundPriority;

    const invalid = ['sales', 'total_sales', 'profit', 'amount', 'quantity', 'value', 'count', 'impact', 'cost', 'discount'];
    const found = keys.find(k => !invalid.includes(k.toLowerCase()) && typeof data[0][k] === 'string');
    return found || 'month';
};

export function AnalysisSection({ type, title, data, loading }) {
    if (loading) return <div className="animate-pulse h-64 bg-slate-800/50 rounded-xl" />

    // Safety check for error object or invalid data
    if (!data) return null;
    if (data.error) {
        return (
            <div className="bg-red-900/20 p-4 rounded-xl border border-red-500/50 my-4">
                <h3 className="text-red-400 font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle size={16} />
                    Analysis Error
                </h3>
                <code className="text-xs text-red-200 block overflow-auto whitespace-pre-wrap">
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

    const isHorizontal = type === 'region' || type === 'rca';

    const commonProps = {
        dataset: normalizedData,
        margin: { top: 10, bottom: 30, left: 70, right: 10 },
        height: 300,
        slotProps: {
            legend: { hidden: true }
        }
    }

    return (
        <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-700/50 my-4 backdrop-blur-sm">
            <h3 className="text-slate-200 font-semibold mb-4 text-sm uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                {title}
            </h3>

            <div style={{ width: '100%', height: 300 }}>
                {type === 'trend' && (
                    <LineChart
                        {...commonProps}
                        xAxis={[{
                            scaleType: 'point',
                            dataKey: labelKey,
                            tickLabelStyle: { fill: '#94a3b8', fontSize: 12 },
                            labelStyle: { fill: '#94a3b8' }
                        }]}
                        yAxis={[{
                            labelStyle: { fill: '#94a3b8' },
                            tickLabelStyle: { fill: '#94a3b8', fontSize: 12 }
                        }]}
                        series={[
                            {
                                dataKey: metricKey,
                                area: true,
                                color: '#818cf8',
                                showMark: false,
                            }
                        ]}
                        grid={{ vertical: false, horizontal: true }}
                        sx={{
                            '.MuiChartsAxis-line': { stroke: '#475569' },
                            '.MuiChartsAxis-tick': { stroke: '#475569' },
                        }}
                    />
                )}

                {(type === 'region' || type === 'aggregate' || type === 'rca' || type === 'products') && (
                    <BarChart
                        {...commonProps}
                        layout={isHorizontal ? 'horizontal' : 'vertical'}
                        xAxis={isHorizontal ?
                            [{ tickLabelStyle: { fill: '#94a3b8', fontSize: 12 } }] :
                            [{ scaleType: 'band', dataKey: labelKey, tickLabelStyle: { fill: '#94a3b8', fontSize: 12 } }]
                        }
                        yAxis={isHorizontal ?
                            [{ scaleType: 'band', dataKey: labelKey, tickLabelStyle: { fill: '#94a3b8', fontSize: 12 } }] :
                            [{ tickLabelStyle: { fill: '#94a3b8', fontSize: 12 } }]
                        }
                        series={[{ dataKey: metricKey, color: '#22d3ee' }]}
                        sx={{
                            '.MuiChartsAxis-line': { stroke: '#475569' },
                            '.MuiChartsAxis-tick': { stroke: '#475569' },
                        }}
                    />
                )}

                {type === 'distribution' && (
                    <PieChart
                        series={[
                            {
                                data: data.map((d, i) => ({
                                    id: i,
                                    value: d[metricKey],
                                    label: d[labelKey]
                                })),
                                innerRadius: 30,
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
                                position: { vertical: 'middle', horizontal: 'right' },
                                labelStyle: { fill: '#e2e8f0', fontSize: 12 }
                            }
                        }}
                    />
                )}

                {type === 'scatter' && (
                    <LineChart
                        {...commonProps}
                        xAxis={[{
                            scaleType: 'point',
                            dataKey: labelKey,
                            tickLabelStyle: { fill: '#94a3b8', fontSize: 12 },
                            labelStyle: { fill: '#94a3b8' }
                        }]}
                        yAxis={[{
                            labelStyle: { fill: '#94a3b8' },
                            tickLabelStyle: { fill: '#94a3b8', fontSize: 12 }
                        }]}
                        series={[
                            {
                                dataKey: metricKey,
                                color: '#f472b6',
                                showMark: true,
                                showLine: false,
                            }
                        ]}
                        grid={{ vertical: true, horizontal: true }}
                        sx={{
                            '.MuiChartsAxis-line': { stroke: '#475569' },
                            '.MuiChartsAxis-tick': { stroke: '#475569' },
                        }}
                    />
                )}

                {type === 'decline' && (
                    <div style={{ height: '100%', overflowY: 'auto', paddingRight: '0.5rem' }}>
                        {data.map((item, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 mb-2 bg-slate-800/50 rounded border border-red-900/20">
                                <span className="text-slate-300">{item.category}</span>
                                <div className="text-right">
                                    <span className="text-red-400 font-mono block">{item.sales_change}%</span>
                                    <span className="text-xs text-slate-500">Drop</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
