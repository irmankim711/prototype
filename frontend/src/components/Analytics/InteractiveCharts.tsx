import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { analyticsService } from "../../services/analyticsService";
import type { ChartData } from "../../services/analyticsService";

interface InteractiveChartsProps {
  defaultChartType?: string;
}

export const InteractiveCharts: React.FC<InteractiveChartsProps> = ({
  defaultChartType = "submissions-trend",
}) => {
  const [selectedChart, setSelectedChart] = useState(defaultChartType);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30);

  const chartOptions = [
    { value: "submissions-trend", label: "Submission Trends" },
    { value: "time-distribution", label: "Time Distribution" },
    { value: "top-forms", label: "Top Performing Forms" },
    { value: "performance-comparison", label: "Performance Comparison" },
    { value: "geographic", label: "Geographic Distribution" },
  ];

  const timeRangeOptions = [
    { value: 7, label: "Last 7 days" },
    { value: 30, label: "Last 30 days" },
    { value: 90, label: "Last 3 months" },
    { value: 180, label: "Last 6 months" },
  ];

  const colors = [
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#ff7300",
    "#00ff00",
    "#ff0000",
    "#00ffff",
    "#ff00ff",
    "#ffff00",
    "#0000ff",
  ];

  const fetchChartData = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      let data: ChartData;

      switch (selectedChart) {
        case "submissions-trend":
          data = await analyticsService.getSubmissionTrendChart(timeRange);
          break;
        case "time-distribution":
          data = await analyticsService.getTimeDistributionChart();
          break;
        case "top-forms":
          data = await analyticsService.getTopFormsChart(5);
          break;
        case "performance-comparison":
          data = await analyticsService.getPerformanceComparisonChart();
          break;
        case "geographic":
          data = await analyticsService.getGeographicChart();
          break;
        default:
          throw Error("Invalid chart type");
      }

      setChartData(data);
    } catch (err) {
      console.error("Error fetching chart data:", err);
      setError("Failed to load chart data");
    } finally {
      setLoading(false);
    }
  }, [selectedChart, timeRange]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  const handleChartChange = (event: SelectChangeEvent<string>) => {
    setSelectedChart(event.target.value);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent<number>) => {
    setTimeRange(event.target.value as number);
  };

  const renderChart = () => {
    if (!chartData) return null;

    // Transform data for Recharts format
    const transformedData = chartData.data.labels.map((label, index) => {
      const dataPoint: Record<string, string | number> = { name: label };

      chartData.data.datasets.forEach((dataset, datasetIndex) => {
        const key = dataset.label || `dataset${datasetIndex}`;
        dataPoint[key] = dataset.data[index] || 0;
      });

      return dataPoint;
    });

    switch (chartData.type) {
      case "line":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={transformedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartData.data.datasets.map((dataset, index) => (
                <Line
                  key={index}
                  type="monotone"
                  dataKey={dataset.label || `dataset${index}`}
                  stroke={dataset.borderColor || colors[index % colors.length]}
                  strokeWidth={2}
                  dot={{
                    fill: dataset.borderColor || colors[index % colors.length],
                  }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case "bar":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={transformedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartData.data.datasets.map((dataset, index) => (
                <Bar
                  key={index}
                  dataKey={dataset.label || `dataset${index}`}
                  fill={
                    Array.isArray(dataset.backgroundColor)
                      ? dataset.backgroundColor[0]
                      : dataset.backgroundColor || colors[index % colors.length]
                  }
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case "doughnut":
      case "pie": {
        const pieData = chartData.data.labels.map((label, index) => ({
          name: label,
          value: chartData.data.datasets[0]?.data[index] || 0,
        }));

        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${((percent || 0) * 100).toFixed(0)}%`
                }
              >
                {pieData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={colors[index % colors.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      }

      default:
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={transformedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartData.data.datasets.map((dataset, index) => (
                <Area
                  key={index}
                  type="monotone"
                  dataKey={dataset.label || `dataset${index}`}
                  stroke={dataset.borderColor || colors[index % colors.length]}
                  fill={
                    Array.isArray(dataset.backgroundColor)
                      ? dataset.backgroundColor[0]
                      : dataset.backgroundColor || colors[index % colors.length]
                  }
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <Card>
      <CardContent>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={3}
        >
          <Typography variant="h6">Interactive Analytics Charts</Typography>

          <Box display="flex" gap={2}>
            {selectedChart === "submissions-trend" && (
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <Select
                  value={timeRange}
                  onChange={handleTimeRangeChange}
                  displayEmpty
                >
                  {timeRangeOptions.map((option: any) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            <FormControl size="small" sx={{ minWidth: 200 }}>
              <Select
                value={selectedChart}
                onChange={handleChartChange}
                displayEmpty
              >
                {chartOptions.map((option: any) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            height={400}
          >
            <CircularProgress />
          </Box>
        ) : (
          <Box>
            {chartData && (
              <Typography variant="h6" gutterBottom textAlign="center">
                {chartData.title}
              </Typography>
            )}
            {renderChart()}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default InteractiveCharts;
