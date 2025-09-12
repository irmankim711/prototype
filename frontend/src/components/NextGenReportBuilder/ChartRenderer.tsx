/**
 * Real Chart Renderer Component
 * Integrates with Chart.js to render actual charts based on data and configuration
 */

import React, { useMemo, useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie, Doughnut, Scatter, Bubble } from 'react-chartjs-2';
import { Box, Paper, Typography, alpha, useTheme } from '@mui/material';
import { 
  BarChart as BarChartIcon,
  TrendingUp as LineChartIcon,
  PieChart as PieChartIcon,
  ScatterPlot as ScatterChartIcon,
  ShowChart as AreaChartIcon,
  DonutLarge as DonutChartIcon,
} from '@mui/icons-material';
import type { ChartData, ChartConfig } from './types';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ChartRendererProps {
  chartData: ChartData;
  config: ChartConfig;
  height?: number | string;
  width?: number | string;
  onChartClick?: (event: any, elements: any[]) => void;
  onChartHover?: (event: any, elements: any[]) => void;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  config,
  height = 400,
  width = '100%',
  onChartClick,
  onChartHover,
}) => {
  const theme = useTheme();
  const chartRef = useRef<any>(null);

  // Generate color schemes
  const getColorScheme = (scheme: string, datasetCount: number) => {
    const colors = {
      default: [
        theme.palette.primary.main,
        theme.palette.secondary.main,
        theme.palette.success.main,
        theme.palette.warning.main,
        theme.palette.error.main,
        theme.palette.info.main,
      ],
      colorful: [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD',
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA'
      ],
      monochrome: [
        theme.palette.primary.main,
        alpha(theme.palette.primary.main, 0.8),
        alpha(theme.palette.primary.main, 0.6),
        alpha(theme.palette.primary.main, 0.4),
        alpha(theme.palette.primary.main, 0.2),
      ],
      professional: [
        '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E83',
        '#1B998B', '#F4A261', '#E76F51', '#264653', '#2A9D8F'
      ]
    };

    const selectedColors = colors[scheme as keyof typeof colors] || colors.default;
    return Array.from({ length: datasetCount }, (_, i) => 
      selectedColors[i % selectedColors.length]
    );
  };

  // Process chart data with colors
  const processedChartData = useMemo(() => {
    const colors = getColorScheme(config.colorScheme || 'default', chartData.datasets.length);
    
    return {
      ...chartData,
      datasets: chartData.datasets.map((dataset, index) => ({
        ...dataset,
        backgroundColor: dataset.backgroundColor || colors[index],
        borderColor: dataset.borderColor || colors[index],
        fill: config.type === 'area' ? true : dataset.fill,
        tension: config.type === 'line' || config.type === 'area' ? 0.4 : dataset.tension,
        pointRadius: dataset.pointRadius || 4,
        pointHoverRadius: dataset.pointHoverRadius || 6,
      }))
    };
  }, [chartData, config, theme]);

  // Chart options
  const chartOptions = useMemo(() => {
    const baseOptions = {
      responsive: config.responsive !== false,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: !!config.title,
          text: config.title,
          font: {
            size: 16,
            weight: 'bold' as const,
          },
          color: theme.palette.text.primary,
        },
        legend: {
          display: config.showLegend !== false,
          position: 'top' as const,
          labels: {
            color: theme.palette.text.secondary,
            usePointStyle: true,
            padding: 20,
          },
        },
        tooltip: {
          backgroundColor: theme.palette.background.paper,
          titleColor: theme.palette.text.primary,
          bodyColor: theme.palette.text.secondary,
          borderColor: theme.palette.divider,
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
        },
      },
      scales: config.type !== 'pie' && config.type !== 'doughnut' ? {
        x: {
          display: true,
          title: {
            display: !!config.xAxis?.label,
            text: config.xAxis?.label || '',
            color: theme.palette.text.secondary,
          },
          grid: {
            display: config.showGrid !== false,
            color: alpha(theme.palette.divider, 0.3),
          },
          ticks: {
            color: theme.palette.text.secondary,
          },
        },
        y: {
          display: true,
          title: {
            display: !!config.yAxis?.label,
            text: config.yAxis?.label || '',
            color: theme.palette.text.secondary,
          },
          grid: {
            display: config.showGrid !== false,
            color: alpha(theme.palette.divider, 0.3),
          },
          ticks: {
            color: theme.palette.text.secondary,
          },
        },
      } : undefined,
      animation: {
        duration: config.animation !== false ? 1000 : 0,
        easing: 'easeInOutQuart' as const,
      },
      interaction: {
        intersect: false,
        mode: 'index' as const,
      },
      onClick: onChartClick,
      onHover: onChartHover,
    };

    return baseOptions;
  }, [config, theme, onChartClick, onChartHover]);

  // Render chart based on type
  const renderChart = () => {
    const commonProps = {
      ref: chartRef,
      data: processedChartData,
      options: chartOptions,
    };

    switch (config.type) {
      case 'line':
        return <Line {...commonProps} />;
      case 'bar':
        return <Bar {...commonProps} />;
      case 'pie':
        return <Pie {...commonProps} />;
      case 'doughnut':
        return <Doughnut {...commonProps} />;
      case 'scatter':
        return <Scatter {...commonProps} />;
      case 'bubble':
        return <Bubble {...commonProps} />;
      case 'area':
        return <Line {...commonProps} />;
      default:
        return <Line {...commonProps} />;
    }
  };

  // Get chart icon
  const getChartIcon = () => {
    switch (config.type) {
      case 'line':
        return <LineChartIcon />;
      case 'bar':
        return <BarChartIcon />;
      case 'pie':
        return <PieChartIcon />;
      case 'doughnut':
        return <DonutChartIcon />;
      case 'scatter':
        return <ScatterChartIcon />;
      case 'area':
        return <AreaChartIcon />;
      default:
        return <BarChartIcon />;
    }
  };

  // Handle chart errors
  if (!chartData || !chartData.labels || !chartData.datasets) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 3,
          height,
          width,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: alpha(theme.palette.error.main, 0.1),
          border: `1px dashed ${theme.palette.error.main}`,
        }}
      >
        <Box textAlign="center">
          {getChartIcon()}
          <Typography variant="h6" color="error" sx={{ mt: 1 }}>
            Invalid Chart Data
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please check your data configuration
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        height,
        width,
        backgroundColor: 'background.paper',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <Box sx={{ height: '100%', position: 'relative' }}>
        {renderChart()}
      </Box>
    </Paper>
  );
};

export default ChartRenderer;
