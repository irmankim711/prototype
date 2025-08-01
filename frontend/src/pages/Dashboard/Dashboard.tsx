import { useState, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js/auto";
import {
  Box,
  Card,
  Typography,
  Button,
  CircularProgress,
  Grid,
  styled,
  Select,
  MenuItem as MuiMenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import { Refresh } from "@mui/icons-material";
import { Bar, Line } from "react-chartjs-2";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface DashboardStats {
  totalSubmissions: number;
  averageScore: number;
  activeUsers: number;
  topScore: number;
  medianScore: number;
}

interface ChartData {
  name: string;
  score: number;
}

// Styled components for the StratoSys design - Modern, Clean and Vibrant
const PageTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 700,
  fontSize: "1.75rem",
  color: "#0e1c40",
  marginBottom: "1.5rem",
  position: "relative",
  paddingBottom: "0.75rem",
  "&:after": {
    content: '""',
    position: "absolute",
    bottom: 0,
    left: 0,
    width: "60px",
    height: "4px",
    background: "linear-gradient(90deg, #4a69dd, #37cfab)",
    borderRadius: "2px",
  },
}));

const StatCard = styled(Card)(() => ({
  borderRadius: "12px",
  boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
  height: "100%",
  border: "none",
  transition: "transform 0.3s ease, box-shadow 0.3s ease",
  overflow: "hidden",
  "&:hover": {
    transform: "translateY(-5px)",
    boxShadow: "0 12px 40px rgba(0, 0, 0, 0.12)",
  },
}));

const StatValue = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 700,
  fontSize: "2rem",
  color: "#0e1c40",
  marginBottom: "0.5rem",
  lineHeight: 1.2,
}));

const StatLabel = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 500,
  fontSize: "0.95rem",
  color: "#64748b",
}));

const ChartContainer = styled(Box)(() => ({
  backgroundColor: "#fff",
  borderRadius: "12px",
  boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
  padding: "1.5rem",
  border: "none",
  height: "100%",
}));

const StyledSelect = styled(Select)(() => ({
  ".MuiOutlinedInput-notchedOutline": {
    borderColor: "#e2e8f0",
    borderRadius: "8px",
  },
  "&:hover .MuiOutlinedInput-notchedOutline": {
    borderColor: "#cbd5e1",
  },
  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
    borderColor: "#4a69dd",
    borderWidth: "1px",
  },
  "& .MuiSelect-select": {
    paddingTop: "10px",
    paddingBottom: "10px",
  },
  fontFamily: '"Poppins", sans-serif',
  fontSize: "0.9rem",
}));

const StyledFormControl = styled(FormControl)(() => ({
  minWidth: 120,
  marginRight: "0.75rem",
}));

const StyledButton = styled(Button)(() => ({
  borderRadius: "8px",
  boxShadow: "0 4px 10px rgba(74, 105, 221, 0.2)",
  textTransform: "none",
  fontWeight: 500,
  padding: "8px 16px",
  background: "linear-gradient(90deg, #4a69dd, #3a59cd)",
  color: "white",
  "&:hover": {
    background: "linear-gradient(90deg, #3a59cd, #2a49bd)",
    boxShadow: "0 6px 12px rgba(74, 105, 221, 0.3)",
  },
}));

const FileItem = styled(Box)(() => ({
  display: "flex",
  alignItems: "center",
  padding: "12px 16px",
  borderRadius: "8px",
  backgroundColor: "#f8fafc",
  marginBottom: "0.75rem",
  transition: "all 0.2s ease",
  cursor: "pointer",
  border: "1px solid #e2e8f0",
  "&:hover": {
    backgroundColor: "#f1f5f9",
    transform: "translateY(-2px)",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.05)",
    borderColor: "#cbd5e1",
  },
}));

export default function Dashboard() {
  const [chartType, setChartType] = useState<string>("Bar");
  const [field, setField] = useState<string>("Score");
  const [groupBy, setGroupBy] = useState<string>("Name");
  // State for loading indicators when refreshing data
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Mock data for the dashboard
  const stats: DashboardStats = {
    totalSubmissions: 6,
    averageScore: 85.83,
    activeUsers: 6,
    topScore: 92,
    medianScore: 86.5,
  };

  const userData: ChartData[] = [
    { name: "Alice", score: 94 },
    { name: "Bob", score: 85 },
    { name: "Charlie", score: 78 },
    { name: "Diana", score: 92 },
    { name: "Eve", score: 88 },
    { name: "Frank", score: 78 },
  ];

  const timeData = [
    { date: "2025-05-06", score: 82 },
    { date: "2025-05-07", score: 86 },
    { date: "2025-05-08", score: 81 },
    { date: "2025-05-09", score: 85 },
    { date: "2025-05-10", score: 88 },
    { date: "2025-05-11", score: 86 },
  ];

  const handleChartTypeChange = (event: SelectChangeEvent<unknown>) => {
    setChartType(event.target.value as string);
  };

  const handleFieldChange = (event: SelectChangeEvent<unknown>) => {
    setField(event.target.value as string);
  };

  const handleGroupByChange = (event: SelectChangeEvent<unknown>) => {
    setGroupBy(event.target.value as string);
  };

  const refreshCharts = () => {
    // In a real app, this would refetch data
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      console.log("Charts refreshed");
    }, 1000);
  };

  // Bar chart data
  const barChartData = {
    labels: userData.map((user) => user.name),
    datasets: [
      {
        label: "Score by Name",
        data: userData.map((user) => user.score),
        backgroundColor: [
          "#4a69dd",
          "#37cfab",
          "#f87979",
          "#f8d854",
          "#6bdaf7",
          "#8b75d7",
        ],
        borderWidth: 0,
        borderRadius: 4,
      },
    ],
  };

  // Line chart data
  const lineChartData = {
    labels: timeData.map((item) => item.date.split("-").slice(1).join("/")),
    datasets: [
      {
        label: "Average Score",
        data: timeData.map((item) => item.score),
        fill: false,
        borderColor: "#4a90e2",
        tension: 0.1,
        pointBackgroundColor: "#4a90e2",
        pointRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: {
          color: "#e5e5e5",
          drawBorder: false,
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  // Loading state
  if (isLoading && false) {
    // Disabled for now, only using loading indicators in buttons
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress size={40} thickness={4} sx={{ color: "#4a69dd" }} />
      </Box>
    );
  }
  return (
    <Box sx={{ padding: { xs: "16px", sm: "24px" } }}>
      <PageTitle>Admin Dashboard & Analytics</PageTitle>

      {/* Stats Section */}
      <Grid container spacing={3} sx={{ mt: 3, mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <Box
              sx={{
                p: 3,
                display: "flex",
                flexDirection: "column",
                height: "100%",
              }}
            >
              <Box sx={{ mb: 2, display: "flex", alignItems: "center" }}>
                <Box
                  sx={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(74, 105, 221, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mr: 2,
                  }}
                >
                  <Refresh sx={{ color: "#4a69dd", fontSize: "1.25rem" }} />
                </Box>
                <StatLabel>Total Submissions</StatLabel>
              </Box>
              <StatValue>{stats.totalSubmissions}</StatValue>
            </Box>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <Box
              sx={{
                p: 3,
                display: "flex",
                flexDirection: "column",
                height: "100%",
              }}
            >
              <Box sx={{ mb: 2, display: "flex", alignItems: "center" }}>
                <Box
                  sx={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(55, 207, 171, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mr: 2,
                  }}
                >
                  <Refresh sx={{ color: "#37cfab", fontSize: "1.25rem" }} />
                </Box>
                <StatLabel>Average Score</StatLabel>
              </Box>
              <StatValue>{stats.averageScore.toFixed(1)}%</StatValue>
            </Box>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <Box
              sx={{
                p: 3,
                display: "flex",
                flexDirection: "column",
                height: "100%",
              }}
            >
              <Box sx={{ mb: 2, display: "flex", alignItems: "center" }}>
                <Box
                  sx={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(248, 121, 121, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mr: 2,
                  }}
                >
                  <Refresh sx={{ color: "#f87979", fontSize: "1.25rem" }} />
                </Box>
                <StatLabel>Active Users</StatLabel>
              </Box>
              <StatValue>{stats.activeUsers}</StatValue>
            </Box>
          </StatCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard>
            <Box
              sx={{
                p: 3,
                display: "flex",
                flexDirection: "column",
                height: "100%",
              }}
            >
              <Box sx={{ mb: 2, display: "flex", alignItems: "center" }}>
                <Box
                  sx={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(248, 216, 84, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mr: 2,
                  }}
                >
                  <Refresh sx={{ color: "#f8d854", fontSize: "1.25rem" }} />
                </Box>
                <StatLabel>Top Score</StatLabel>
              </Box>
              <StatValue>{stats.topScore}%</StatValue>
            </Box>
          </StatCard>
        </Grid>
      </Grid>

      {/* Chart Controls */}
      <Box
        sx={{
          mt: 4,
          mb: 5,
          p: 3,
          bgcolor: "#f8fafc",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.03)",
        }}
      >
        <Typography
          variant="h6"
          sx={{
            mb: 3,
            fontFamily: '"Poppins", sans-serif',
            fontWeight: 600,
            color: "#0e1c40",
          }}
        >
          Chart Controls
        </Typography>

        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
          <StyledFormControl size="small">
            <InputLabel id="chart-type-label">Chart Type</InputLabel>
            <StyledSelect
              labelId="chart-type-label"
              value={chartType}
              label="Chart Type"
              onChange={handleChartTypeChange}
              sx={{ minWidth: 140 }}
            >
              <MuiMenuItem value="Bar">Bar Chart</MuiMenuItem>
              <MuiMenuItem value="Line">Line Chart</MuiMenuItem>
              <MuiMenuItem value="Pie">Pie Chart</MuiMenuItem>
            </StyledSelect>
          </StyledFormControl>

          <StyledFormControl size="small">
            <InputLabel id="field-label">Field</InputLabel>
            <StyledSelect
              labelId="field-label"
              value={field}
              label="Field"
              onChange={handleFieldChange}
              sx={{ minWidth: 140 }}
            >
              <MuiMenuItem value="Score">Score</MuiMenuItem>
              <MuiMenuItem value="Time">Time</MuiMenuItem>
            </StyledSelect>
          </StyledFormControl>

          <StyledFormControl size="small">
            <InputLabel id="group-by-label">Group By</InputLabel>
            <StyledSelect
              labelId="group-by-label"
              value={groupBy}
              label="Group By"
              onChange={handleGroupByChange}
              sx={{ minWidth: 140 }}
            >
              <MuiMenuItem value="Name">Name</MuiMenuItem>
              <MuiMenuItem value="Date">Date</MuiMenuItem>
            </StyledSelect>
          </StyledFormControl>
        </Box>

        <StyledButton
          startIcon={
            isLoading ? (
              <CircularProgress size={18} color="inherit" />
            ) : (
              <Refresh />
            )
          }
          onClick={refreshCharts}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "Refresh Charts"}
        </StyledButton>
      </Box>

      {/* Charts Section */}
      <Grid container spacing={4} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <ChartContainer>
            <Typography
              variant="h6"
              sx={{
                mb: 3,
                fontFamily: '"Poppins", sans-serif',
                fontWeight: 600,
                color: "#0e1c40",
              }}
            >
              Score by Name
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={barChartData} options={chartOptions} />
            </Box>
          </ChartContainer>
        </Grid>
        <Grid item xs={12} md={6}>
          <ChartContainer>
            <Typography
              variant="h6"
              sx={{
                mb: 3,
                fontFamily: '"Poppins", sans-serif',
                fontWeight: 600,
                color: "#0e1c40",
              }}
            >
              Score Trend Over Time
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line data={lineChartData} options={chartOptions} />
            </Box>
          </ChartContainer>
        </Grid>
      </Grid>

      {/* Previous Files Section */}
      <Box
        sx={{
          mt: 5,
          p: 3,
          backgroundColor: "#ffffff",
          borderRadius: "12px",
          boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
        }}
      >
        <Typography
          variant="h6"
          sx={{
            mb: 3,
            fontFamily: '"Poppins", sans-serif',
            fontWeight: 600,
            color: "#0e1c40",
          }}
        >
          Previous Files
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {[
            { name: "majlis Agama Subang.csv", date: "2025-05-10" },
            { name: "majlis Agama Putrajaya.csv", date: "2025-05-08" },
            { name: "majlis Agama Kajang.csv", date: "2025-05-05" },
          ].map((file, index) => (
            <FileItem key={index}>
              <Box
                sx={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "10px",
                  backgroundColor: "rgba(74, 105, 221, 0.1)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginRight: "16px",
                }}
              >
                <Refresh sx={{ color: "#4a69dd", fontSize: "1.25rem" }} />
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography
                  sx={{
                    fontWeight: 600,
                    color: "#0e1c40",
                    fontSize: "0.95rem",
                  }}
                >
                  {file.name}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: "#64748b",
                    display: "block",
                    marginTop: "4px",
                  }}
                >
                  Last modified: {file.date}
                </Typography>
              </Box>
            </FileItem>
          ))}
        </Box>
        <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
          <StyledButton
            startIcon={
              isLoading ? (
                <CircularProgress size={18} color="inherit" />
              ) : (
                <Refresh />
              )
            }
            onClick={refreshCharts}
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh Data"}
          </StyledButton>
        </Box>
      </Box>
    </Box>
  );
}
