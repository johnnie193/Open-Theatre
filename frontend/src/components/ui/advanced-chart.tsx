import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface DataPoint {
  x: number | string;
  y: number;
  label?: string;
  color?: string;
}

interface AdvancedChartProps {
  data: DataPoint[];
  type: 'line' | 'bar' | 'area' | 'scatter' | 'pie';
  width?: number;
  height?: number;
  className?: string;
  animated?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  xAxisLabel?: string;
  yAxisLabel?: string;
  title?: string;
}

export const AdvancedChart: React.FC<AdvancedChartProps> = ({
  data,
  type,
  width = 400,
  height = 300,
  className,
  animated = true,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  xAxisLabel,
  yAxisLabel,
  title
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredPoint, setHoveredPoint] = useState<DataPoint | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const margin = { top: 20, right: 20, bottom: 40, left: 40 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  const maxY = Math.max(...data.map(d => d.y));
  const minY = Math.min(...data.map(d => d.y));
  const yRange = maxY - minY;

  const getX = (value: number | string, index: number) => {
    if (typeof value === 'number') {
      return (value / (data.length - 1)) * chartWidth;
    }
    return (index / (data.length - 1)) * chartWidth;
  };

  const getY = (value: number) => {
    return chartHeight - ((value - minY) / yRange) * chartHeight;
  };

  const getColor = (index: number, point?: DataPoint) => {
    if (point?.color) return point.color;
    const colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];
    return colors[index % colors.length];
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - margin.left;
    const y = e.clientY - rect.top - margin.top;
    
    setTooltipPosition({ x: e.clientX, y: e.clientY });
    
    // Find closest point
    let closestPoint: DataPoint | null = null;
    let minDistance = Infinity;
    
    data.forEach((point, index) => {
      const pointX = getX(point.x, index);
      const pointY = getY(point.y);
      const distance = Math.sqrt(Math.pow(x - pointX, 2) + Math.pow(y - pointY, 2));
      
      if (distance < minDistance) {
        minDistance = distance;
        closestPoint = point;
      }
    });
    
    setHoveredPoint(closestPoint);
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  const renderLineChart = () => {
    const pathData = data
      .map((point, index) => {
        const x = getX(point.x, index);
        const y = getY(point.y);
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');

    return (
      <motion.path
        d={pathData}
        fill="none"
        stroke="#3B82F6"
        strokeWidth="2"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: animated ? 1 : 0 }}
      />
    );
  };

  const renderBarChart = () => {
    return data.map((point, index) => {
      const x = getX(point.x, index);
      const y = getY(point.y);
      const barWidth = chartWidth / data.length * 0.8;
      const barHeight = chartHeight - y;
      
      return (
        <motion.rect
          key={index}
          x={x - barWidth / 2}
          y={y}
          width={barWidth}
          height={barHeight}
          fill={getColor(index, point)}
          initial={{ height: 0, y: chartHeight }}
          animate={{ height: barHeight, y: y }}
          transition={{ duration: animated ? 0.5 : 0, delay: index * 0.1 }}
        />
      );
    });
  };

  const renderAreaChart = () => {
    const pathData = data
      .map((point, index) => {
        const x = getX(point.x, index);
        const y = getY(point.y);
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ') + ` L ${getX(data[data.length - 1].x, data.length - 1)} ${chartHeight} L ${getX(data[0].x, 0)} ${chartHeight} Z`;

    return (
      <motion.path
        d={pathData}
        fill="url(#gradient)"
        stroke="#3B82F6"
        strokeWidth="2"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: animated ? 1 : 0 }}
      />
    );
  };

  const renderScatterPlot = () => {
    return data.map((point, index) => {
      const x = getX(point.x, index);
      const y = getY(point.y);
      
      return (
        <motion.circle
          key={index}
          cx={x}
          cy={y}
          r="4"
          fill={getColor(index, point)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: animated ? 0.3 : 0, delay: index * 0.05 }}
        />
      );
    });
  };

  const renderPieChart = () => {
    const total = data.reduce((sum, point) => sum + point.y, 0);
    let currentAngle = 0;
    const radius = Math.min(chartWidth, chartHeight) / 2;
    const centerX = chartWidth / 2;
    const centerY = chartHeight / 2;

    return data.map((point, index) => {
      const percentage = point.y / total;
      const angle = percentage * 360;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      
      const x1 = centerX + radius * Math.cos((startAngle - 90) * Math.PI / 180);
      const y1 = centerY + radius * Math.sin((startAngle - 90) * Math.PI / 180);
      const x2 = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
      const y2 = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);
      
      const largeArcFlag = angle > 180 ? 1 : 0;
      const pathData = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
      
      currentAngle += angle;
      
      return (
        <motion.path
          key={index}
          d={pathData}
          fill={getColor(index, point)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: animated ? 0.5 : 0, delay: index * 0.1 }}
        />
      );
    });
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return renderLineChart();
      case 'bar':
        return renderBarChart();
      case 'area':
        return renderAreaChart();
      case 'scatter':
        return renderScatterPlot();
      case 'pie':
        return renderPieChart();
      default:
        return null;
    }
  };

  return (
    <div className={cn("relative", className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          {title}
        </h3>
      )}
      
      <div className="relative">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="border border-gray-200 dark:border-gray-700 rounded-lg"
        >
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            {/* Grid */}
            {showGrid && (
              <g className="text-gray-300 dark:text-gray-600">
                {Array.from({ length: 5 }, (_, i) => {
                  const y = (i / 4) * chartHeight;
                  return (
                    <line
                      key={i}
                      x1="0"
                      y1={y}
                      x2={chartWidth}
                      y2={y}
                      stroke="currentColor"
                      strokeWidth="0.5"
                      opacity="0.3"
                    />
                  );
                })}
                {Array.from({ length: 5 }, (_, i) => {
                  const x = (i / 4) * chartWidth;
                  return (
                    <line
                      key={i}
                      x1={x}
                      y1="0"
                      x2={x}
                      y2={chartHeight}
                      stroke="currentColor"
                      strokeWidth="0.5"
                      opacity="0.3"
                    />
                  );
                })}
              </g>
            )}
            
            {/* Chart */}
            {renderChart()}
            
            {/* Axes */}
            <g className="text-gray-600 dark:text-gray-400">
              <line
                x1="0"
                y1="0"
                x2="0"
                y2={chartHeight}
                stroke="currentColor"
                strokeWidth="2"
              />
              <line
                x1="0"
                y1={chartHeight}
                x2={chartWidth}
                y2={chartHeight}
                stroke="currentColor"
                strokeWidth="2"
              />
            </g>
            
            {/* Labels */}
            {xAxisLabel && (
              <text
                x={chartWidth / 2}
                y={chartHeight + 30}
                textAnchor="middle"
                className="text-sm fill-gray-600 dark:fill-gray-400"
              >
                {xAxisLabel}
              </text>
            )}
            {yAxisLabel && (
              <text
                x={-20}
                y={chartHeight / 2}
                textAnchor="middle"
                transform="rotate(-90, -20, 150)"
                className="text-sm fill-gray-600 dark:fill-gray-400"
              >
                {yAxisLabel}
              </text>
            )}
          </g>
        </svg>
        
        {/* Tooltip */}
        {showTooltip && hoveredPoint && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg pointer-events-none z-10"
            style={{
              left: tooltipPosition.x + 10,
              top: tooltipPosition.y - 10
            }}
          >
            <div className="text-sm">
              <div className="font-medium">{hoveredPoint.label || 'Data Point'}</div>
              <div>X: {hoveredPoint.x}</div>
              <div>Y: {hoveredPoint.y}</div>
            </div>
          </motion.div>
        )}
      </div>
      
      {/* Legend */}
      {showLegend && type !== 'pie' && (
        <div className="flex flex-wrap gap-4 mt-4">
          {data.map((point, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getColor(index, point) }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {point.label || `Series ${index + 1}`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
