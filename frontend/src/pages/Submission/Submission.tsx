import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  styled,
  Chip,
  Pagination,
  FormControl,
  CircularProgress,
  Alert,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import {
  formBuilderAPI,
  type FormSubmission,
} from "../../services/formBuilder";

// Styled components
const PageTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: "1.5rem",
  color: "#333",
  marginBottom: "1rem",
  borderBottom: "2px solid #1e3a8a",
  paddingBottom: "0.5rem",
  display: "inline-block",
}));

const StyledTableContainer = styled(TableContainer)(() => ({
  borderRadius: "4px",
  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
  marginTop: "1.5rem",
  border: "1px solid #eaeaea",
}));

const StyledTableHead = styled(TableHead)(() => ({
  backgroundColor: "#f8f9fa",
}));

const StyledTableCell = styled(TableCell)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 500,
  fontSize: "0.9rem",
  padding: "12px 16px",
  borderBottom: "1px solid #eaeaea",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:hover": {
    backgroundColor: "#f5f7fa",
  },
}));

const ScoreChip = styled(Chip)<{ score: number }>(({ score }) => {
  let backgroundColor = "#4caf50";
  let color = "white";

  if (score < 80) {
    backgroundColor = "#ff9800";
  }
  if (score < 70) {
    backgroundColor = "#f44336";
  }

  return {
    fontWeight: 600,
    fontSize: "0.85rem",
    backgroundColor,
    color,
    height: "28px",
    width: "28px",
    borderRadius: "50%",
    ".MuiChip-label": {
      padding: "0px",
    },
  };
});

const ViewButton = styled(Button)(() => ({
  backgroundColor: "#3f51b5",
  borderRadius: "4px",
  textTransform: "none",
  fontWeight: 500,
  fontSize: "0.9rem",
  "&:hover": {
    backgroundColor: "#303f9f",
  },
}));

const ExportButton = styled(Button)(() => ({
  backgroundColor: "#3f51b5",
  borderRadius: "4px",
  textTransform: "none",
  fontWeight: 500,
  "&:hover": {
    backgroundColor: "#303f9f",
  },
}));

interface Submission {
  id: string | number;
  name: string;
  email: string;
  date: string;
  score: number;
  status?: string;
  form_title?: string;
}

interface PaginationInfo {
  page: number;
  pages: number;
  per_page: number;
  total: number;
  has_next: boolean;
  has_prev: boolean;
}

export default function SubmissionPage() {
  const [filter, setFilter] = useState<string>("All Submissions");
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    pages: 1,
    per_page: 10,
    total: 0,
    has_next: false,
    has_prev: false,
  });
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Fetch submissions data
  const fetchSubmissions = async (page: number = 1, statusFilter?: string) => {
    try {
      setLoading(true);
      setError(null);

      const params: {
        page: number;
        per_page: number;
        status?: string;
        date_from?: string;
      } = {
        page,
        per_page: 10,
      };

      // Apply status filter
      if (statusFilter && statusFilter !== "All Submissions") {
        switch (statusFilter) {
          case "Recent": {
            // For recent, we can use date filter for last 7 days
            const recentDate = new Date();
            recentDate.setDate(recentDate.getDate() - 7);
            params.date_from = recentDate.toISOString();
            break;
          }
          case "High Score":
            // We'll filter this on the frontend since score is calculated
            break;
          case "Low Score":
            // We'll filter this on the frontend since score is calculated
            break;
          default:
            params.status = statusFilter.toLowerCase();
        }
      }

      const response = await formBuilderAPI.getAllSubmissions(params);

      let filteredSubmissions = response.submissions || [];

      // Apply frontend filters for score-based filtering
      if (statusFilter === "High Score") {
        filteredSubmissions = filteredSubmissions.filter(
          (sub: FormSubmission) => (sub.score || 0) >= 80
        );
      } else if (statusFilter === "Low Score") {
        filteredSubmissions = filteredSubmissions.filter(
          (sub: FormSubmission) => (sub.score || 0) < 70
        );
      }

      setSubmissions(filteredSubmissions);
      setPagination(
        response.pagination || {
          page: 1,
          pages: 1,
          per_page: 10,
          total: filteredSubmissions.length,
          has_next: false,
          has_prev: false,
        }
      );
    } catch (err) {
      console.error("Error fetching submissions:", err);
      setError("Failed to load submissions. Please try again.");
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  // Load submissions on component mount and when filters change
  useEffect(() => {
    fetchSubmissions(currentPage, filter);
  }, [currentPage, filter]);

  const handleFilterChange = (event: SelectChangeEvent<string>) => {
    const newFilter = event.target.value as string;
    setFilter(newFilter);
    setCurrentPage(1); // Reset to first page when filter changes
  };

  const handlePageChange = (
    _event: React.ChangeEvent<unknown>,
    page: number
  ) => {
    setCurrentPage(page);
  };

  const handleExport = async () => {
    try {
      setLoading(true);

      // Get all submissions for export
      const response = await formBuilderAPI.getAllSubmissions({
        page: 1,
        per_page: 1000, // Get all submissions
      });

      if (response.submissions && response.submissions.length > 0) {
        // Create CSV content
        const headers = ["Name", "Email", "Date", "Score", "Form", "Status"];
        const csvContent = [
          headers.join(","),
          ...response.submissions.map((sub: FormSubmission) =>
            [
              `"${sub.name || "Anonymous"}"`,
              `"${sub.email || "No email"}"`,
              `"${new Date(
                sub.date || sub.submitted_at
              ).toLocaleDateString()}"`,
              sub.score || 0,
              `"${sub.form_title || "Unknown Form"}"`,
              `"${sub.status || "submitted"}"`,
            ].join(",")
          ),
        ].join("\n");

        // Create and download file
        const blob = new Blob([csvContent], {
          type: "text/csv;charset=utf-8;",
        });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute(
          "download",
          `submissions_export_${new Date().toISOString().split("T")[0]}.csv`
        );
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log(`Exported ${response.submissions.length} submissions`);
      } else {
        console.log("No submissions to export");
      }
    } catch (err) {
      console.error("Export failed:", err);
      setError("Failed to export submissions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchSubmissions(currentPage, filter);
  };

  const handleViewSubmission = (submission: Submission) => {
    // For now, just log the submission details
    console.log("Viewing submission:", submission);

    // In a full implementation, this would open a detailed view modal
    alert(
      `Submission Details:\n\nName: ${submission.name}\nEmail: ${
        submission.email
      }\nScore: ${submission.score}\nForm: ${
        submission.form_title
      }\nDate: ${new Date(submission.date).toLocaleString()}`
    );
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <PageTitle>Submission</PageTitle>

      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <Select
            value={filter}
            onChange={handleFilterChange}
            displayEmpty
            sx={{
              fontFamily: '"Poppins", sans-serif',
              fontSize: "0.9rem",
              ".MuiOutlinedInput-notchedOutline": {
                borderColor: "#ccc",
              },
            }}
          >
            <MenuItem value="All Submissions">All Submissions</MenuItem>
            <MenuItem value="Recent">Recent</MenuItem>
            <MenuItem value="High Score">High Score</MenuItem>
            <MenuItem value="Low Score">Low Score</MenuItem>
          </Select>
        </FormControl>

        <ExportButton
          variant="contained"
          startIcon={<i className="fas fa-file-export"></i>}
          onClick={handleExport}
          disabled={loading}
        >
          Export
        </ExportButton>

        <Button
          variant="outlined"
          startIcon={<i className="fas fa-refresh"></i>}
          onClick={handleRefresh}
          disabled={loading}
          sx={{ ml: 1 }}
        >
          Refresh
        </Button>
      </Box>

      <StyledTableContainer>
        <Box sx={{ p: 2, borderBottom: "1px solid #eaeaea" }}>
          <Typography variant="h6" sx={{ fontWeight: 500 }}>
            Recent Submissions
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Showing {submissions.length} of {pagination.total} submissions
          </Typography>
        </Box>
        <Table>
          <StyledTableHead>
            <TableRow>
              <StyledTableCell>Name</StyledTableCell>
              <StyledTableCell>Email</StyledTableCell>
              <StyledTableCell>Date</StyledTableCell>
              <StyledTableCell>Score</StyledTableCell>
              <StyledTableCell>Form</StyledTableCell>
              <StyledTableCell>Action</StyledTableCell>
            </TableRow>
          </StyledTableHead>
          <TableBody>
            {submissions.length === 0 ? (
              <StyledTableRow>
                <StyledTableCell colSpan={6} align="center">
                  <Typography variant="body2" color="textSecondary">
                    No submissions found
                  </Typography>
                </StyledTableCell>
              </StyledTableRow>
            ) : (
              submissions.map((submission: Submission) => (
                <StyledTableRow key={submission.id}>
                  <StyledTableCell>{submission.name}</StyledTableCell>
                  <StyledTableCell>{submission.email}</StyledTableCell>
                  <StyledTableCell>
                    {new Date(submission.date).toLocaleDateString()}
                  </StyledTableCell>
                  <StyledTableCell>
                    <ScoreChip
                      label={submission.score}
                      score={submission.score}
                      size="small"
                    />
                  </StyledTableCell>
                  <StyledTableCell>
                    <Typography variant="body2" sx={{ fontSize: "0.85rem" }}>
                      {submission.form_title || "Unknown Form"}
                    </Typography>
                  </StyledTableCell>
                  <StyledTableCell>
                    <ViewButton
                      variant="contained"
                      size="small"
                      onClick={() => handleViewSubmission(submission)}
                    >
                      View
                    </ViewButton>
                  </StyledTableCell>
                </StyledTableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
          <Pagination
            count={pagination.pages}
            page={currentPage}
            onChange={handlePageChange}
            shape="rounded"
            size="small"
          />
        </Box>
      </StyledTableContainer>
    </Box>
  );
}
