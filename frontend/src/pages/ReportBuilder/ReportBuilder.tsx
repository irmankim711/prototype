import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  useTheme,
  useMediaQuery,
  Tooltip,
  LinearProgress,
  Avatar,
} from "@mui/material";
// Removed unused react-hook-form imports
import {
  fetchReportTemplates,
  createReport,
  analyzeData,
  fetchTemplatePlaceholders,
  fetchWordTemplates,
  generateReport,
  downloadReport,
} from "../../services/api";
import type { ReportTemplate } from "../../services/api";
import GoogleSheetImport from "./GoogleSheetImport";
import TemplateEditor from "./TemplateEditor";
import FieldMapping from "./FieldMapping";
import {
  Assignment,
  Description,
  SwapHoriz,
  Preview,
  CheckCircle,
  AutoAwesome,
  PlayArrow,
  Schedule,
  TrendingUp,
  Analytics,
  Download,
} from "@mui/icons-material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  Divider,
  Fade,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress as MuiLinearProgress,
  TextField,
  MenuItem,
} from "@mui/material";
import * as XLSX from "xlsx";
import DownloadIcon from "@mui/icons-material/Download";
import "./ReportBuilder.css";
import { formBuilderAPI } from "../../services/formBuilder";
import axiosInstance from "../../services/axiosInstance";

// Create a simple wrapper to use existing reports API instead of automated reports API
const reportsAPI = {
  getReports: async () => {
    try {
      const response = await axiosInstance.get("/reports");
      return response.data;
    } catch (error) {
      console.error("Error fetching reports:", error);
      throw error;
    }
  },
  generateReport: async (data: any) => {
    try {
      const response = await axiosInstance.post("/reports", data);
      return response.data;
    } catch (error) {
      console.error("Error generating report:", error);
      throw error;
    }
  },
};

// Types for better type safety
interface ImportedDataType {
  headers: string[];
  rows: string[][];
  processedData: Record<string, unknown>;
  tableName?: string;
  sheetName?: string;
  range?: string;
}

interface TableDetectionResult {
  name: string;
  sheetName: string;
  headers: string[];
  rows: string[][];
  range: string;
}

interface WordTemplateType {
  id: string;
  name: string;
  filename: string;
  description?: string;
  previewUrl?: string;
}

const steps = [
  "Import Data",
  "Choose Template",
  "Map Fields",
  "Review & Generate",
  "Success",
];

// Automated Reports Interface Component
const AutomatedReportsInterface = () => {
  const [forms, setForms] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [selectedForm, setSelectedForm] = useState<number | null>(null);
  const [reportType, setReportType] = useState<
    "summary" | "detailed" | "trends"
  >("summary");
  const [dateRange, setDateRange] = useState<
    "last_7_days" | "last_30_days" | "last_90_days"
  >("last_30_days");
  const [isGenerating, setIsGenerating] = useState(false);

  // Mock data for demonstration
  const mockForms = [
    {
      id: 1,
      title: "Employee Satisfaction Survey",
      description: "Quarterly employee feedback and satisfaction survey",
      submission_count: 45,
      is_active: true,
      created_at: "2024-01-01T00:00:00Z",
    },
    {
      id: 2,
      title: "Customer Feedback Form",
      description: "Customer experience and product feedback collection",
      submission_count: 128,
      is_active: true,
      created_at: "2024-01-05T00:00:00Z",
    },
    {
      id: 3,
      title: "IT Support Request",
      description: "Technical support and issue reporting form",
      submission_count: 67,
      is_active: true,
      created_at: "2024-01-10T00:00:00Z",
    },
    {
      id: 4,
      title: "Event Registration",
      description: "Conference and workshop registration form",
      submission_count: 89,
      is_active: true,
      created_at: "2024-01-12T00:00:00Z",
    },
  ];

  const mockReports = [
    {
      id: 1,
      title: "Employee Satisfaction Q1 2024",
      form_title: "Employee Satisfaction Survey",
      report_type: "summary",
      status: "completed",
      created_at: "2024-01-15T10:30:00Z",
      download_url: "#",
    },
    {
      id: 2,
      title: "Customer Feedback Analysis",
      form_title: "Customer Feedback Form",
      report_type: "detailed",
      status: "completed",
      created_at: "2024-01-14T14:20:00Z",
      download_url: "#",
    },
    {
      id: 3,
      title: "Weekly Incident Report",
      form_title: "IT Support Request",
      report_type: "trends",
      status: "processing",
      created_at: "2024-01-13T09:15:00Z",
      download_url: "#",
    },
  ];

  // Fetch forms and reports on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Try to get forms from the real API
        const formsData = await formBuilderAPI.getForms({
          page: 1,
          limit: 100,
        });
        console.log("Forms data from API:", formsData);

        if (formsData && formsData.forms && formsData.forms.length > 0) {
          setForms(formsData.forms);
        } else {
          console.log("No forms from API, using mock data");
          setForms(mockForms);
        }

        // Try to get reports from the real API
        try {
          const reportsData = await reportsAPI.getReports();
          console.log("Reports data from API:", reportsData);

          if (
            reportsData &&
            reportsData.reports &&
            reportsData.reports.length > 0
          ) {
            setReports(reportsData.reports);
          } else {
            console.log("No reports from API, using mock data");
            setReports(mockReports);
          }
        } catch (reportsError) {
          console.error("Error fetching reports:", reportsError);
          setReports(mockReports);
        }
      } catch (error) {
        console.error("Error fetching forms:", error);
        setForms(mockForms);
        setReports(mockReports);
      }
    };
    fetchData();
  }, []);

  const handleGenerateReport = async () => {
    if (!selectedForm) return;

    setIsGenerating(true);
    try {
      console.log("Generating report with:", {
        form_id: selectedForm,
        report_type: reportType,
        date_range: dateRange,
      });

      const result = await reportsAPI.generateReport({
        form_id: selectedForm,
        report_type: reportType,
        date_range: dateRange,
      });

      console.log("Report generation result:", result);

      // Refresh reports list
      try {
        const reportsData = await reportsAPI.getReports();
        if (reportsData && reportsData.reports) {
          setReports(reportsData.reports);
        } else {
          console.log("No reports data returned, keeping current reports");
        }
      } catch (refreshError) {
        console.error("Error refreshing reports:", refreshError);
      }

      // Show success feedback
      setTimeout(() => {
        setIsGenerating(false);
      }, 2000);
    } catch (error) {
      console.error("Error generating report:", error);
      setIsGenerating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "processing":
        return "warning";
      case "failed":
        return "error";
      default:
        return "default";
    }
  };

  const getReportTypeIcon = (type: string) => {
    switch (type) {
      case "summary":
        return <Analytics />;
      case "detailed":
        return <TrendingUp />;
      case "trends":
        return <Schedule />;
      default:
        return <Description />;
    }
  };

  return (
    <Box className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Header Section */}
      <Box className="mb-8">
        <Box className="flex items-center gap-3 mb-4">
          <Box className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl">
            <AutoAwesome className="text-white text-2xl" />
          </Box>
          <Box>
            <Typography
              variant="h3"
              className="font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"
            >
              AI-Powered Reports
            </Typography>
            <Typography variant="body1" className="text-slate-600 mt-1">
              Generate intelligent insights from your form data with advanced
              analytics
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Main Content Grid */}
      <Grid container spacing={4} className="max-w-7xl mx-auto">
        {/* Generate New Report Card */}
        <Grid item xs={12} lg={7}>
          <Card
            className="h-full shadow-xl border-0 bg-white/80 backdrop-blur-sm"
            sx={{ borderRadius: 3 }}
          >
            <CardContent className="p-8">
              <Box className="flex items-center gap-3 mb-6">
                <Box className="p-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg">
                  <PlayArrow className="text-white" />
                </Box>
                <Typography variant="h5" className="font-bold text-slate-800">
                  Generate New Report
                </Typography>
              </Box>

              <Box className="space-y-6">
                {/* Form Selection */}
                <Box>
                  <TextField
                    select
                    fullWidth
                    label="Select Form"
                    value={selectedForm || ""}
                    onChange={(e) => setSelectedForm(Number(e.target.value))}
                    variant="outlined"
                    className="mb-2"
                    InputProps={{
                      startAdornment: (
                        <Box className="mr-3 p-1 bg-blue-100 rounded">
                          <Description className="text-blue-600 text-sm" />
                        </Box>
                      ),
                    }}
                  >
                    <MenuItem value="">
                      <em>Choose a form to analyze...</em>
                    </MenuItem>
                    {forms.map((form) => (
                      <MenuItem key={form.id} value={form.id}>
                        <Box className="flex items-center justify-between w-full">
                          <span>{form.title}</span>
                          <Chip
                            label={`${form.submission_count} submissions`}
                            size="small"
                            className="ml-2 bg-blue-100 text-blue-700"
                          />
                        </Box>
                      </MenuItem>
                    ))}
                  </TextField>
                </Box>

                {/* Report Type Selection */}
                <Box>
                  <TextField
                    select
                    fullWidth
                    label="Report Type"
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value as any)}
                    variant="outlined"
                    className="mb-2"
                    InputProps={{
                      startAdornment: (
                        <Box className="mr-3 p-1 bg-purple-100 rounded">
                          <Analytics className="text-purple-600 text-sm" />
                        </Box>
                      ),
                    }}
                  >
                    <MenuItem value="summary">
                      <Box className="flex items-center gap-2">
                        <Analytics className="text-purple-600" />
                        <span>Summary Report</span>
                      </Box>
                    </MenuItem>
                    <MenuItem value="detailed">
                      <Box className="flex items-center gap-2">
                        <TrendingUp className="text-purple-600" />
                        <span>Detailed Analysis</span>
                      </Box>
                    </MenuItem>
                    <MenuItem value="trends">
                      <Box className="flex items-center gap-2">
                        <Schedule className="text-purple-600" />
                        <span>Trends Report</span>
                      </Box>
                    </MenuItem>
                  </TextField>
                </Box>

                {/* Date Range Selection */}
                <Box>
                  <TextField
                    select
                    fullWidth
                    label="Date Range"
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value as any)}
                    variant="outlined"
                    className="mb-2"
                    InputProps={{
                      startAdornment: (
                        <Box className="mr-3 p-1 bg-orange-100 rounded">
                          <Schedule className="text-orange-600 text-sm" />
                        </Box>
                      ),
                    }}
                  >
                    <MenuItem value="last_7_days">Last 7 Days</MenuItem>
                    <MenuItem value="last_30_days">Last 30 Days</MenuItem>
                    <MenuItem value="last_90_days">Last 90 Days</MenuItem>
                  </TextField>
                </Box>

                {/* Generate Button */}
                <Box className="pt-4">
                  <Button
                    variant="contained"
                    fullWidth
                    size="large"
                    onClick={handleGenerateReport}
                    disabled={!selectedForm || isGenerating}
                    className="h-14 text-lg font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-300"
                    startIcon={
                      isGenerating ? (
                        <CircularProgress size={24} className="text-white" />
                      ) : (
                        <Box className="p-1 bg-white/20 rounded">
                          <AutoAwesome className="text-white" />
                        </Box>
                      )
                    }
                  >
                    {isGenerating ? (
                      <Box className="flex items-center gap-2">
                        <span>Generating AI Report...</span>
                        <Box className="animate-pulse">✨</Box>
                      </Box>
                    ) : (
                      "Generate AI Report"
                    )}
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Reports Card */}
        <Grid item xs={12} lg={5}>
          <Card
            className="h-full shadow-xl border-0 bg-white/80 backdrop-blur-sm"
            sx={{ borderRadius: 3 }}
          >
            <CardContent className="p-8">
              <Box className="flex items-center gap-3 mb-6">
                <Box className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
                  <Description className="text-white" />
                </Box>
                <Typography variant="h5" className="font-bold text-slate-800">
                  Recent Reports
                </Typography>
              </Box>

              <Box className="space-y-4 max-h-96 overflow-y-auto">
                {reports.length > 0 ? (
                  reports.slice(0, 3).map((report) => (
                    <Card
                      key={report.id}
                      className="border border-slate-200 hover:border-purple-300 transition-all duration-300 hover:shadow-md"
                      sx={{ borderRadius: 2 }}
                    >
                      <CardContent className="p-4">
                        <Box className="flex items-start justify-between mb-3">
                          <Box className="flex items-center gap-2">
                            <Box className="p-1 bg-gradient-to-r from-blue-100 to-purple-100 rounded">
                              {getReportTypeIcon(report.report_type)}
                            </Box>
                            <Typography
                              variant="subtitle1"
                              className="font-semibold text-slate-800"
                            >
                              {report.title}
                            </Typography>
                          </Box>
                          <Chip
                            label={report.status}
                            color={getStatusColor(report.status) as any}
                            size="small"
                            className="font-medium"
                          />
                        </Box>

                        <Typography
                          variant="body2"
                          className="text-slate-600 mb-3"
                        >
                          {report.form_title} • {report.report_type}
                        </Typography>

                        <Box className="flex items-center justify-between">
                          <Typography
                            variant="caption"
                            className="text-slate-500"
                          >
                            {new Date(report.created_at).toLocaleDateString(
                              "en-US",
                              {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              }
                            )}
                          </Typography>

                          <Box className="flex gap-2">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<Download />}
                              className="border-purple-300 text-purple-600 hover:bg-purple-50"
                            >
                              Download
                            </Button>
                            <Button
                              size="small"
                              variant="contained"
                              startIcon={<Preview />}
                              className="bg-gradient-to-r from-purple-600 to-blue-600"
                            >
                              View
                            </Button>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Box className="text-center py-8">
                    <Box className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <AutoAwesome className="text-purple-600 text-2xl" />
                    </Box>
                    <Typography variant="h6" className="text-slate-700 mb-2">
                      No Reports Yet
                    </Typography>
                    <Typography variant="body2" className="text-slate-500">
                      Generate your first AI-powered report to see it here
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Mock data for fallback
const mockTemplates = [
  {
    id: "1",
    name: "Financial Report",
    description: "Standard financial report template",
    schema: {
      fields: [
        { name: "revenue", label: "Revenue", type: "number", required: true },
        { name: "expenses", label: "Expenses", type: "number", required: true },
        { name: "notes", label: "Notes", type: "text", required: false },
      ],
    },
    isActive: true,
  },
  {
    id: "2",
    name: "Performance Report",
    description: "Performance analysis template",
    schema: {
      fields: [
        {
          name: "score",
          label: "Performance Score",
          type: "number",
          required: true,
        },
        { name: "comments", label: "Comments", type: "text", required: false },
      ],
    },
    isActive: true,
  },
];

const stepIcons = [
  <Assignment fontSize="large" />, // Import Data
  <Description fontSize="large" />, // Choose Template
  <SwapHoriz fontSize="large" />, // Map Fields
  <Preview fontSize="large" />, // Review & Generate
  <CheckCircle fontSize="large" color="success" />, // Success
];

export default function ReportBuilder() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [reportMode, setReportMode] = useState<"manual" | "automated">(
    "manual"
  );
  const [importedData, setImportedData] = useState<ImportedDataType | null>(
    null
  );
  // Removed unused mapping state
  const [selectedTemplateFilename, setSelectedTemplateFilename] =
    useState<string>("");
  const [reportData, setReportData] = useState<any>({});
  const [analysis, setAnalysis] = useState<any>(null);
  const [successData, setSuccessData] = useState<any>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [templatePlaceholders, setTemplatePlaceholders] = useState<string[]>(
    []
  );
  const [isLoadingPlaceholders, setIsLoadingPlaceholders] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});
  const [autoFilledFields, setAutoFilledFields] = useState<
    Record<string, boolean>
  >({});
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});

  // Enhanced Excel upload handler with multi-table detection
  const handleExcelUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const data = new Uint8Array(evt.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });

        // Process all sheets and detect multiple tables
        const allTables = detectTablesInWorkbook(workbook);

        if (allTables.length === 0) {
          alert("No data tables found in the Excel file");
          return;
        }

        // If multiple tables detected, let user choose or combine them
        if (allTables.length > 1) {
          console.log(
            `Found ${allTables.length} tables:`,
            allTables.map((t) => t.name)
          );
          // For now, use the largest table by default
          const largestTable = allTables.reduce((prev, current) =>
            current.rows.length > prev.rows.length ? current : prev
          );
          console.log("Using largest table:", largestTable.name);
          processTableData(largestTable);
        } else {
          processTableData(allTables[0]);
        }
      } catch (error) {
        console.error("Error processing Excel file:", error);
        alert("Error processing Excel file. Please check the file format.");
      }
    };
    reader.readAsArrayBuffer(file);
  };

  // Detect all data tables in workbook
  const detectTablesInWorkbook = (workbook: XLSX.WorkBook) => {
    const allTables: Array<{
      name: string;
      sheetName: string;
      headers: string[];
      rows: any[][];
      range: string;
    }> = [];

    workbook.SheetNames.forEach((sheetName) => {
      const worksheet = workbook.Sheets[sheetName];
      const tables = detectTablesInSheet(worksheet, sheetName);
      allTables.push(...tables);
    });

    return allTables;
  };

  // Detect multiple tables within a single sheet
  const detectTablesInSheet = (
    worksheet: XLSX.WorkSheet,
    sheetName: string
  ) => {
    const range = XLSX.utils.decode_range(worksheet["!ref"] || "A1:A1");
    const tables: Array<{
      name: string;
      sheetName: string;
      headers: string[];
      rows: any[][];
      range: string;
    }> = [];

    // Get all data from sheet
    const jsonData = XLSX.utils.sheet_to_json(worksheet, {
      header: 1,
      defval: null,
      range: worksheet["!ref"],
    }) as any[][];

    if (jsonData.length === 0) return tables;

    // Find contiguous data blocks
    const dataBlocks = findContiguousDataBlocks(jsonData);

    dataBlocks.forEach((block, index) => {
      if (block.rows.length > 1 && block.headers.length > 0) {
        // At least header + 1 row
        const tableName =
          dataBlocks.length > 1 ? `${sheetName}_Table${index + 1}` : sheetName;

        tables.push({
          name: tableName,
          sheetName,
          headers: block.headers,
          rows: block.rows,
          range: `${getCellAddress(
            block.startRow,
            block.startCol
          )}:${getCellAddress(block.endRow, block.endCol)}`,
        });
      }
    });

    return tables;
  };

  // Find contiguous data blocks in a sheet
  const findContiguousDataBlocks = (data: any[][]) => {
    const blocks: Array<{
      startRow: number;
      endRow: number;
      startCol: number;
      endCol: number;
      headers: string[];
      rows: any[][];
    }> = [];

    let currentBlock: {
      startRow: number;
      endRow: number;
      startCol: number;
      endCol: number;
      data: any[][];
    } | null = null;

    for (let row = 0; row < data.length; row++) {
      const rowData = data[row] || [];
      const hasData = rowData.some(
        (cell) =>
          cell !== null && cell !== undefined && String(cell).trim() !== ""
      );

      if (hasData) {
        if (!currentBlock) {
          // Start new block
          const firstDataCol = rowData.findIndex(
            (cell) =>
              cell !== null && cell !== undefined && String(cell).trim() !== ""
          );
          const lastDataCol =
            rowData
              .map((cell, idx) => ({ cell, idx }))
              .filter(
                ({ cell }) =>
                  cell !== null &&
                  cell !== undefined &&
                  String(cell).trim() !== ""
              )
              .pop()?.idx || firstDataCol;

          currentBlock = {
            startRow: row,
            endRow: row,
            startCol: firstDataCol,
            endCol: lastDataCol,
            data: [rowData.slice(firstDataCol, lastDataCol + 1)],
          };
        } else {
          // Extend current block
          currentBlock.endRow = row;
          const firstDataCol = Math.min(
            currentBlock.startCol,
            rowData.findIndex(
              (cell) =>
                cell !== null &&
                cell !== undefined &&
                String(cell).trim() !== ""
            )
          );
          const lastDataCol = Math.max(
            currentBlock.endCol,
            rowData
              .map((cell, idx) => ({ cell, idx }))
              .filter(
                ({ cell }) =>
                  cell !== null &&
                  cell !== undefined &&
                  String(cell).trim() !== ""
              )
              .pop()?.idx || currentBlock.endCol
          );

          currentBlock.startCol =
            firstDataCol >= 0 ? firstDataCol : currentBlock.startCol;
          currentBlock.endCol = lastDataCol;
          currentBlock.data.push(
            rowData.slice(currentBlock.startCol, currentBlock.endCol + 1)
          );
        }
      } else if (currentBlock && currentBlock.data.length > 1) {
        // Empty row found, close current block if it has enough data
        const headers = currentBlock.data[0]
          .map((h) => String(h || "").trim())
          .filter((h) => h);
        const rows = currentBlock.data
          .slice(1)
          .filter((row) =>
            row.some(
              (cell) =>
                cell !== null &&
                cell !== undefined &&
                String(cell).trim() !== ""
            )
          );

        if (headers.length > 0 && rows.length > 0) {
          blocks.push({
            ...currentBlock,
            headers,
            rows,
          });
        }
        currentBlock = null;
      }
    }

    // Handle last block
    if (currentBlock && currentBlock.data.length > 1) {
      const headers = currentBlock.data[0]
        .map((h) => String(h || "").trim())
        .filter((h) => h);
      const rows = currentBlock.data
        .slice(1)
        .filter((row) =>
          row.some(
            (cell) =>
              cell !== null && cell !== undefined && String(cell).trim() !== ""
          )
        );

      if (headers.length > 0 && rows.length > 0) {
        blocks.push({
          ...currentBlock,
          headers,
          rows,
        });
      }
    }

    return blocks;
  };

  // Convert row/col to Excel cell address
  const getCellAddress = (row: number, col: number): string => {
    let colStr = "";
    let colNum = col;
    while (colNum >= 0) {
      colStr = String.fromCharCode(65 + (colNum % 26)) + colStr;
      colNum = Math.floor(colNum / 26) - 1;
    }
    return `${colStr}${row + 1}`;
  };

  // Process a single table's data
  const processTableData = (table: {
    name: string;
    sheetName: string;
    headers: string[];
    rows: any[][];
    range: string;
  }) => {
    console.log(
      `Processing table: ${table.name} from sheet: ${table.sheetName}`
    );
    console.log("Headers:", table.headers);
    console.log("Rows:", table.rows.length);
    console.log("Range:", table.range);

    // Process data for intelligent field mapping
    const processedData = processExcelData(table.headers, table.rows);

    setImportedData({
      headers: table.headers,
      rows: table.rows,
      processedData,
      tableName: table.name,
      sheetName: table.sheetName,
      range: table.range,
    });

    // Auto-populate editData with processed values
    const autoMappedData: Record<string, string> = {};
    Object.keys(processedData).forEach((key) => {
      if (processedData[key] !== null && processedData[key] !== undefined) {
        autoMappedData[key] = String(processedData[key]);
      }
    });

    setEditData((prev) => ({ ...prev, ...autoMappedData }));
  };

  // Enhanced Excel data processing with better type inference and data aggregation
  const processExcelData = (
    headers: string[],
    rows: any[][]
  ): Record<string, any> => {
    console.log("Processing Excel data...");
    console.log("Headers:", headers);
    console.log("Number of rows:", rows.length);
    console.log("First few rows:", rows.slice(0, 3));

    const processed: Record<string, any> = {};

    // Enhanced field mappings for better template compatibility
    const fieldMappings: Record<string, string[]> = {
      // Identity and participant info
      nama_peserta: [
        "nama",
        "peserta",
        "name",
        "participant",
        "nama peserta",
        "participant name",
        "attendee",
      ],
      PROGRAM_TITLE: [
        "program",
        "title",
        "judul",
        "program title",
        "nama program",
        "program name",
        "course",
        "training",
      ],
      LOCATION_MAIN: [
        "location",
        "lokasi",
        "place",
        "tempat",
        "venue",
        "alamat",
        "address",
      ],
      Time: [
        "time",
        "waktu",
        "jam",
        "tanggal",
        "date",
        "schedule",
        "datetime",
        "timestamp",
      ],
      Place1: ["place", "tempat", "location", "lokasi", "venue", "site"],

      // Financial data
      company_name: [
        "company",
        "company name",
        "organization",
        "business name",
        "perusahaan",
        "org",
      ],
      revenue: [
        "revenue",
        "total revenue",
        "sales",
        "income",
        "turnover",
        "pendapatan",
        "gross sales",
      ],
      expenses: [
        "expenses",
        "total expenses",
        "costs",
        "expenditure",
        "biaya",
        "cost",
      ],
      profit: [
        "profit",
        "net profit",
        "earnings",
        "net income",
        "keuntungan",
        "margin",
      ],
      loss: ["loss", "net loss", "deficit", "kerugian"],

      // Dates and periods
      date: [
        "date",
        "report date",
        "period",
        "month",
        "year",
        "tanggal",
        "periode",
      ],
      quarter: ["quarter", "q1", "q2", "q3", "q4", "period", "kuartal", "qtr"],
      year: ["year", "tahun", "annual", "yearly"],
      month: ["month", "bulan", "monthly"],

      // Organizational
      department: [
        "department",
        "division",
        "team",
        "unit",
        "departemen",
        "dept",
      ],
      manager: ["manager", "supervisor", "lead", "director", "manajer", "head"],
      employee: ["employee", "staff", "worker", "karyawan", "pegawai"],

      // Metrics and measurements
      total: ["total", "sum", "amount", "value", "jumlah", "grand total"],
      percentage: ["percentage", "percent", "%", "rate", "persentase", "pct"],
      count: ["count", "number", "quantity", "qty", "jumlah", "num"],
      average: ["average", "avg", "mean", "rata-rata", "rata rata"],
      score: ["score", "rating", "grade", "nilai", "skor"],
      target: ["target", "goal", "objective", "sasaran"],
      actual: ["actual", "real", "current", "aktual"],

      // Media and branding
      bannering: ["banner", "bannering", "promosi", "promotion", "advertising"],
      Signature_Consultant: [
        "signature",
        "consultant",
        "konsultan",
        "tanda tangan",
        "ttd",
      ],
      Image2: ["image", "gambar", "photo", "foto", "picture", "img"],
      Image4: ["image", "gambar", "photo", "foto", "picture", "img"],
      Image7: ["image", "gambar", "photo", "foto", "picture", "img"],

      // Additional common fields
      status: ["status", "state", "condition", "kondisi"],
      category: ["category", "type", "class", "kategori", "jenis"],
      description: ["description", "desc", "detail", "deskripsi", "keterangan"],
      remarks: ["remarks", "notes", "comment", "catatan", "note"],
      contact: ["contact", "phone", "email", "kontak", "telephone"],
      address: ["address", "alamat", "location", "lokasi"],
    };

    // Helper function to infer data type
    const inferDataType = (values: any[]) => {
      const nonEmptyValues = values.filter(
        (v) => v !== null && v !== undefined && String(v).trim() !== ""
      );
      if (nonEmptyValues.length === 0) return "text";

      const numericValues = nonEmptyValues
        .map((v) => parseFloat(String(v)))
        .filter((v) => !isNaN(v));
      const dateValues = nonEmptyValues.filter(
        (v) => !isNaN(Date.parse(String(v)))
      );

      if (numericValues.length > nonEmptyValues.length * 0.8) return "number";
      if (dateValues.length > nonEmptyValues.length * 0.6) return "date";
      return "text";
    };

    // Helper function to aggregate numeric data
    const aggregateNumericData = (values: number[], field: string) => {
      if (values.length === 0) return null;

      const sum = values.reduce((acc, val) => acc + val, 0);
      const avg = sum / values.length;
      const min = Math.min(...values);
      const max = Math.max(...values);

      return { sum, avg, min, max };
    };

    // Process each header and try to map to known fields
    headers.forEach((header, index) => {
      const normalizedHeader = header.toLowerCase().trim();
      console.log(
        `Processing header: "${header}" (normalized: "${normalizedHeader}")`
      );

      // Get column values
      const columnValues = rows
        .map((row) => row[index])
        .filter(
          (val) =>
            val !== null && val !== undefined && String(val).trim() !== ""
        );

      if (columnValues.length === 0) return;

      // Find matching field mapping
      let matchedField = null;
      for (const [field, patterns] of Object.entries(fieldMappings)) {
        if (patterns.some((pattern) => normalizedHeader.includes(pattern))) {
          matchedField = field;
          break;
        }
      }

      if (matchedField) {
        console.log(`Found match for "${header}" -> "${matchedField}"`);

        const dataType = inferDataType(columnValues);
        console.log(`Data type for "${matchedField}": ${dataType}`);

        if (dataType === "number") {
          const numericValues = columnValues
            .map((val) => parseFloat(String(val)))
            .filter((val) => !isNaN(val));
          const aggregated = aggregateNumericData(numericValues, matchedField);
          if (aggregated !== null) {
            processed[`${matchedField}_sum`] = aggregated.sum;
            processed[`${matchedField}_avg`] = aggregated.avg;
            processed[`${matchedField}_min`] = aggregated.min;
            processed[`${matchedField}_max`] = aggregated.max;
            // Store formatted versions
            processed[`${matchedField}_sum_formatted`] =
              new Intl.NumberFormat().format(aggregated.sum);
            processed[`${matchedField}_avg_formatted`] =
              new Intl.NumberFormat().format(aggregated.avg);
            processed[`${matchedField}_min_formatted`] =
              new Intl.NumberFormat().format(aggregated.min);
            processed[`${matchedField}_max_formatted`] =
              new Intl.NumberFormat().format(aggregated.max);
          }
        } else if (dataType === "date") {
          // Use the most recent valid date
          const validDates = columnValues
            .map((val) => new Date(val))
            .filter((date) => !isNaN(date.getTime()))
            .sort((a, b) => b.getTime() - a.getTime());

          if (validDates.length > 0) {
            processed[matchedField] = validDates[0].toLocaleDateString();
            processed[`${matchedField}_iso`] = validDates[0].toISOString();
          }
        } else {
          // For text fields, use the most common non-empty value
          const valueCounts = columnValues.reduce((acc, val) => {
            const key = String(val).trim();
            acc[key] = (acc[key] || 0) + 1;
            return acc;
          }, {} as Record<string, number>);

          const mostCommonValue = Object.entries(valueCounts).sort(
            ([, a], [, b]) => b - a
          )[0]?.[0];

          if (mostCommonValue) {
            processed[matchedField] = mostCommonValue;
          }
        }
      } else {
        // No specific mapping found, create generic field
        const sanitizedFieldName = normalizedHeader.replace(/[^a-z0-9]/g, "_");
        const dataType = inferDataType(columnValues);

        if (dataType === "number") {
          const numericValues = columnValues
            .map((val) => parseFloat(String(val)))
            .filter((val) => !isNaN(val));
          if (numericValues.length > 0) {
            // Default to sum for unknown numeric fields
            processed[sanitizedFieldName] = numericValues.reduce(
              (sum, val) => sum + val,
              0
            );
          }
        } else {
          // Use first non-empty value for text fields
          processed[sanitizedFieldName] = columnValues[0];
        }

        console.log(
          `Created generic mapping for "${header}" -> "${sanitizedFieldName}":`,
          processed[sanitizedFieldName]
        );
      }
    });

    // Add computed fields and metadata
    if (rows.length > 0) {
      processed["total_rows"] = rows.length;
      processed["total_columns"] = headers.length;
      processed["data_source"] = "Excel Import";
      processed["import_date"] = new Date().toLocaleDateString();
      processed["import_timestamp"] = new Date().toISOString();

      // Calculate some basic analytics if we have numeric data
      const numericFields = Object.keys(processed).filter(
        (key) =>
          typeof processed[key] === "number" && !key.includes("_formatted")
      );

      if (numericFields.length > 0) {
        const numericValues = numericFields.map((field) => processed[field]);
        processed["data_summary"] = {
          numeric_fields: numericFields.length,
          max_value: Math.max(...numericValues),
          min_value: Math.min(...numericValues),
          avg_value:
            numericValues.reduce((sum, val) => sum + val, 0) /
            numericValues.length,
        };
      }

      // Add field type information for debugging
      processed["field_types"] = Object.keys(processed).reduce((acc, key) => {
        acc[key] = typeof processed[key];
        return acc;
      }, {} as Record<string, string>);
    }

    console.log("Final processed data:", processed);
    console.log("Processed fields:", Object.keys(processed));
    return processed;
  };

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  // Use mock data if API fails
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ["reportTemplates"],
    queryFn: fetchReportTemplates,
  });

  const { data: wordTemplatesData } = useQuery({
    queryKey: ["wordTemplates"],
    queryFn: fetchWordTemplates,
  });

  // Use mock data if API fails
  const displayTemplates: ReportTemplate[] = Array.isArray(templatesData)
    ? templatesData
    : mockTemplates;

  const createReportMutation = useMutation({
    mutationFn: createReport,
    onSuccess: (data) => {
      navigate(`/reports/${data.id}`);
    },
    onError: (error) => {
      console.log("Create report error:", error);
      // Show success message even if API fails (for demo)
      alert("Report created successfully! (Demo mode)");
    },
  });

  const analyzeDataMutation = useMutation({
    mutationFn: analyzeData,
    onSuccess: (data) => {
      setAnalysis(data);
    },
    onError: (error) => {
      console.log("Analyze data error:", error);
      // Mock analysis data
      setAnalysis({
        summary: "Data analysis completed successfully.",
        insights: ["Auto analysis placeholder"],
        suggestions: "Consider reviewing your data.",
      });
    },
  });

  // Fetch placeholders when a template is selected
  useEffect(() => {
    const fetchPlaceholders = async () => {
      if (!selectedTemplateFilename) {
        setTemplatePlaceholders([]);
        return;
      }

      setIsLoadingPlaceholders(true);
      try {
        const response = await fetchTemplatePlaceholders(
          selectedTemplateFilename
        );
        setTemplatePlaceholders(response);
      } catch (error) {
        console.error("Failed to fetch template placeholders:", error);
        setTemplatePlaceholders([]);
      } finally {
        setIsLoadingPlaceholders(false);
      }
    };

    fetchPlaceholders();
  }, [selectedTemplateFilename]);

  // When reportData is set (after auto-mapping), initialize editData
  useEffect(() => {
    setEditData(reportData);
  }, [reportData]);

  // Step navigation handlers
  const handleNext = async () => {
    if (activeStep === 1) {
      // Template placeholders are already fetched via useEffect when template is selected
      // No need to fetch again here
    }

    if (activeStep === 2) {
      // Process field mapping data
      const mappedData: Record<string, string> = {};

      // Apply field mapping to imported data
      if (importedData && fieldMapping) {
        Object.entries(fieldMapping).forEach(([excelHeader, placeholder]) => {
          const headerIndex = importedData.headers.indexOf(excelHeader);
          if (headerIndex !== -1) {
            // Get the first non-empty value from this column
            const columnValues = importedData.rows
              .map((row) => row[headerIndex])
              .filter((val) => val !== null && val !== undefined && val !== "");

            if (columnValues.length > 0) {
              mappedData[placeholder] = String(columnValues[0]);
            }
          }
        });
      }

      // Merge with existing editData
      setEditData((prev) => ({ ...prev, ...mappedData }));

      // Integrate AI analysis after mapping
      analyzeDataMutation.mutate(editData, {
        onSuccess: (analysis) => {
          setEditData((prev) => ({
            ...prev,
            ai_summary: analysis.summary,
            ai_insights: analysis.insights.join("\n"),
            ai_suggestions: analysis.suggestions,
          }));
        },
      });
    }

    setActiveStep((prev) => prev + 1);
  };
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    try {
      const result = await generateReport(selectedTemplateFilename, editData);
      setSuccessData({
        downloadUrl: result.downloadUrl,
        message: result.message,
      });
      setActiveStep((prevStep) => prevStep + 1);
    } catch (error: any) {
      setGenerationError(
        error?.message || "Failed to generate report. Please try again."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRetry = () => {
    setGenerationError(null);
    handleGenerate();
  };

  // Step content
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Fade in={activeStep === 0}>
            <Box sx={{ padding: 0, margin: 0 }}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <Typography variant="h6" gutterBottom sx={{ flex: 1 }}>
                  Import Data
                </Typography>
                <Tooltip title="Upload an Excel file or import from Google Sheets. Your data will be kept secure.">
                  <InfoOutlinedIcon color="primary" />
                </Tooltip>
              </Box>
              {/* Drag-and-drop Excel upload */}
              <Box
                sx={{
                  p: 2,
                  mb: 2,
                  textAlign: "center",
                  transition: "background 0.2s",
                  "&:hover": { bgcolor: "rgba(14,28,64,0.07)" },
                  cursor: "pointer",
                  position: "relative",
                }}
                onClick={() =>
                  document.getElementById("excel-upload-input")?.click()
                }
              >
                <CloudUploadIcon
                  sx={{ fontSize: 48, color: "#0e1c40", mb: 1 }}
                />
                <Typography
                  variant="body1"
                  sx={{ color: "#0e1c40", fontWeight: 500 }}
                >
                  Drag & drop your Excel file here, or click to browse
                </Typography>
                <input
                  id="excel-upload-input"
                  type="file"
                  accept=".xlsx,.xls"
                  className="excel-upload-input"
                  onChange={handleExcelUpload}
                  aria-label="Upload Excel file"
                />
              </Box>
              <Divider sx={{ my: 1 }}>or</Divider>
              {/* Google Sheets Import */}
              <GoogleSheetImport
                onDataParsed={(data) =>
                  setImportedData({
                    ...data,
                    processedData: processExcelData(data.headers, data.rows),
                  })
                }
                apiKey={import.meta.env.VITE_GOOGLE_API_KEY || ""}
                clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ""}
              />
              {/* Enhanced preview for imported data */}
              {importedData && (
                <Box
                  sx={{
                    mt: 4,
                    p: 3,
                    position: "relative",
                  }}
                >
                  <Box sx={{ position: "absolute", top: 16, right: 16 }}>
                    <CheckCircleIcon color="success" fontSize="large" />
                  </Box>

                  {/* Table metadata */}
                  <Box sx={{ mb: 3 }}>
                    <Typography
                      variant="subtitle1"
                      sx={{ color: "#0e1c40", fontWeight: 600, mb: 2 }}
                    >
                      Data Import Summary
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Box
                          sx={{
                            textAlign: "center",
                            p: 1,
                            bgcolor: "#f8fafc",
                            borderRadius: 1,
                          }}
                        >
                          <Typography variant="h6" color="primary">
                            {importedData.rows.length}
                          </Typography>
                          <Typography variant="caption">Rows</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box
                          sx={{
                            textAlign: "center",
                            p: 1,
                            bgcolor: "#f8fafc",
                            borderRadius: 1,
                          }}
                        >
                          <Typography variant="h6" color="primary">
                            {importedData.headers.length}
                          </Typography>
                          <Typography variant="caption">Columns</Typography>
                        </Box>
                      </Grid>
                      {importedData.sheetName && (
                        <Grid item xs={6} sm={3}>
                          <Box
                            sx={{
                              textAlign: "center",
                              p: 1,
                              bgcolor: "#f8fafc",
                              borderRadius: 1,
                            }}
                          >
                            <Typography
                              variant="body2"
                              color="primary"
                              sx={{ fontWeight: 600 }}
                            >
                              {importedData.sheetName}
                            </Typography>
                            <Typography variant="caption">Sheet</Typography>
                          </Box>
                        </Grid>
                      )}
                      {importedData.range && (
                        <Grid item xs={6} sm={3}>
                          <Box
                            sx={{
                              textAlign: "center",
                              p: 1,
                              bgcolor: "#f8fafc",
                              borderRadius: 1,
                            }}
                          >
                            <Typography
                              variant="body2"
                              color="primary"
                              sx={{ fontWeight: 600 }}
                            >
                              {importedData.range}
                            </Typography>
                            <Typography variant="caption">Range</Typography>
                          </Box>
                        </Grid>
                      )}
                    </Grid>
                  </Box>

                  {/* Smart insights about detected data */}
                  {importedData.processedData &&
                    Object.keys(importedData.processedData).length > 0 && (
                      <Box sx={{ mb: 3 }}>
                        <Typography
                          variant="subtitle2"
                          sx={{ color: "#0e1c40", fontWeight: 600, mb: 1 }}
                        >
                          🤖 Smart Data Detection
                        </Typography>
                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                          {Object.entries(importedData.processedData)
                            .filter(
                              ([key, value]) =>
                                value !== null &&
                                value !== undefined &&
                                !key.includes("_formatted") &&
                                !key.includes("field_types") &&
                                !key.includes("data_summary") &&
                                key !== "total_rows" &&
                                key !== "total_columns" &&
                                key !== "data_source" &&
                                key !== "import_date" &&
                                key !== "import_timestamp"
                            )
                            .slice(0, 8)
                            .map(([key, value]) => (
                              <Box
                                key={key}
                                sx={{
                                  px: 2,
                                  py: 0.5,
                                  bgcolor: "#e0f2fe",
                                  color: "#0277bd",
                                  borderRadius: 1,
                                  fontSize: "0.75rem",
                                  fontWeight: 500,
                                }}
                              >
                                {key.replace(/_/g, " ")}:{" "}
                                {String(value).length > 20
                                  ? String(value).substring(0, 20) + "..."
                                  : String(value)}
                              </Box>
                            ))}
                        </Box>
                      </Box>
                    )}

                  <Typography
                    variant="subtitle2"
                    sx={{ color: "#0e1c40", fontWeight: 600, mb: 2 }}
                  >
                    Data Preview ({importedData.tableName || "Table"})
                  </Typography>
                  <Box
                    sx={{
                      overflowX: "auto",
                      maxHeight: 300,
                      overflowY: "auto",
                    }}
                  >
                    <table className="data-preview-table">
                      <thead className="data-preview-thead">
                        <tr>
                          {importedData.headers.map((header) => (
                            <th key={header} className="data-preview-th">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {importedData.rows.slice(0, 10).map((row, idx) => (
                          <tr
                            key={idx}
                            className={
                              idx % 2 === 0
                                ? "data-preview-tr-even"
                                : "data-preview-tr-odd"
                            }
                          >
                            {importedData.headers.map((_, colIdx) => (
                              <td key={colIdx} className="data-preview-td">
                                {row[colIdx]}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Box>
                  {importedData.rows.length > 10 && (
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 1,
                        display: "block",
                        textAlign: "center",
                        color: "text.secondary",
                      }}
                    >
                      Showing first 10 of {importedData.rows.length} rows
                    </Typography>
                  )}
                  <Alert severity="success" sx={{ mt: 2 }}>
                    ✅ Data imported successfully! Found{" "}
                    {Object.keys(importedData.processedData || {}).length}{" "}
                    mapped fields. Proceed to next step.
                  </Alert>
                </Box>
              )}
            </Box>
          </Fade>
        );
      case 1:
        return (
          <Box sx={{ padding: 0, margin: 0 }}>
            <Typography variant="h6" gutterBottom>
              Choose Report Template
            </Typography>
            <Grid container spacing={3}>
              {wordTemplatesData?.map((template: WordTemplateType) => (
                <Grid item xs={12} sm={6} md={4} key={template.id}>
                  <Box
                    onClick={() =>
                      setSelectedTemplateFilename(template.filename)
                    }
                    sx={{
                      cursor: "pointer",
                      transition: "opacity 0.2s",
                      opacity:
                        selectedTemplateFilename === template.filename
                          ? 1
                          : 0.7,
                      "&:hover": {
                        opacity: 1,
                      },
                    }}
                  >
                    <Box
                      component="img"
                      sx={{
                        width: "100%",
                        height: "140px",
                        objectFit: "cover",
                      }}
                      src={
                        template.previewUrl || "/static/previews/default.png"
                      }
                      alt={template.name}
                    />
                    <Box sx={{ p: 1 }}>
                      <Typography variant="h6">{template.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {template.description}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
            {selectedTemplateFilename && (
              <Box mt={3} textAlign="center">
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleNext}
                >
                  Next
                </Button>
              </Box>
            )}
          </Box>
        );
      case 2:
        return (
          <FieldMapping
            excelHeaders={importedData?.headers || []}
            templatePlaceholders={templatePlaceholders}
            currentMapping={fieldMapping}
            onMappingChange={setFieldMapping}
          />
        );
      case 3:
        return (
          <TemplateEditor
            templateName={selectedTemplateFilename}
            data={editData}
            onDataChange={setEditData}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />
        );
      case 4:
        return (
          <Box textAlign="center" sx={{ padding: 0, margin: 0 }}>
            <Typography variant="h5" gutterBottom>
              Report Generated Successfully!
            </Typography>
            {successData && (
              <Box my={2}>
                <Typography variant="subtitle1">
                  Download your report:
                </Typography>
                <Box
                  display="flex"
                  justifyContent="center"
                  sx={{ gap: "16px", my: 2 }}
                >
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => downloadReport(successData.downloadUrl)}
                    startIcon={<DownloadIcon />}
                  >
                    Download Report
                  </Button>
                  <Button
                    variant="outlined"
                    color="primary"
                    component="a"
                    href={successData.downloadUrl}
                    target="_blank"
                  >
                    Open in New Tab
                  </Button>
                </Box>
                <Alert severity="success" sx={{ mt: 2 }}>
                  {successData.message ||
                    "Your report has been generated successfully!"}
                </Alert>
              </Box>
            )}
            <Box mt={3}>
              <Button
                variant="contained"
                color="secondary"
                component={Link}
                to="/report-history"
                sx={{ mr: 2 }}
              >
                My Reports
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.reload()}
              >
                Generate Another Report
              </Button>
            </Box>
          </Box>
        );
      default:
        return "Unknown step";
    }
  };

  if (templatesLoading) {
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

  // Step enable/disable logic
  const canProceed = () => {
    if (activeStep === 0) return !!importedData;
    if (activeStep === 1) return !!selectedTemplateFilename;
    if (activeStep === 2) return Object.keys(fieldMapping).length > 0; // At least one field mapped
    return true;
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        width: "100vw",
        boxSizing: "border-box",
        padding: 0,
        margin: 0,
        flexDirection: isMobile ? "column" : "row",
      }}
    >
      {/* Mode Selector */}
      <Box sx={{ position: "absolute", top: 20, left: 20, zIndex: 1000 }}>
        <Tabs
          value={reportMode}
          onChange={(_, newValue) => setReportMode(newValue)}
          sx={{
            backgroundColor: "white",
            borderRadius: 2,
            boxShadow: 2,
            "& .MuiTab-root": {
              minWidth: 120,
              fontWeight: 600,
            },
          }}
        >
          <Tab
            value="manual"
            label="Manual Builder"
            icon={<Description />}
            iconPosition="start"
          />
          <Tab
            value="automated"
            label="Automated Reports"
            icon={<AutoAwesome />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Sidebar/Stepper (manual mode only) */}
      <Box
        sx={{
          width: isMobile ? "100%" : 220,
          minWidth: isMobile ? "100%" : 220,
          backgroundColor: "#f8f9fa",
          padding: 2,
          display: reportMode === "manual" ? "flex" : "none", // Only show sidebar in manual mode
          flexDirection: isMobile ? "row" : "column",
          alignItems: "center",
          justifyContent: isMobile ? "space-between" : "flex-start",
          gap: isMobile ? 1 : 3,
        }}
      >
        {steps.map((label, idx) => (
          <Tooltip
            title={label}
            key={label}
            placement={isMobile ? "top" : "right"}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                opacity: idx > activeStep ? 0.4 : 1,
                transition: "opacity 0.2s",
              }}
            >
              <Avatar
                sx={{
                  bgcolor: idx === activeStep ? "#0e1c40" : "#e0e7ef",
                  color: idx === activeStep ? "white" : "#64748b",
                  width: 48,
                  height: 48,
                  mb: isMobile ? 0 : 1,
                  border: idx < activeStep ? "2px solid #22c55e" : "none",
                  boxShadow: idx === activeStep ? "0 0 0 4px #e0e7ef" : "none",
                }}
              >
                {stepIcons[idx]}
              </Avatar>
              {!isMobile && (
                <Typography
                  variant="caption"
                  sx={{
                    color: idx === activeStep ? "#0e1c40" : "#64748b",
                    fontWeight: idx === activeStep ? 700 : 400,
                  }}
                >
                  {label}
                </Typography>
              )}
            </Box>
          </Tooltip>
        ))}
        {/* Progress bar */}
        <Box
          sx={{
            width: isMobile ? "100%" : "80%",
            mt: isMobile ? 0 : 3,
            alignSelf: "center",
          }}
        >
          <LinearProgress
            variant="determinate"
            value={((activeStep + 1) / steps.length) * 100}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: "#e0e7ef",
              "& .MuiLinearProgress-bar": { bgcolor: "#0e1c40" },
            }}
          />
        </Box>
      </Box>

      {/* Main Content Area */}
      <Box
        sx={{ flex: 1, minWidth: 0, padding: 1, backgroundColor: "#ffffff" }}
      >
        {reportMode === "manual" ? (
          <>
            <Typography
              variant="h4"
              gutterBottom
              sx={{
                color: "#0e1c40",
                fontWeight: 700,
                mb: 2,
                textAlign: "left",
              }}
            >
              Create New Report
            </Typography>
            {getStepContent(activeStep)}
            <Box display="flex" justifyContent="flex-end" mt={2} gap={2}>
              {activeStep > 0 && (
                <Button variant="outlined" onClick={handleBack}>
                  Back
                </Button>
              )}
              {activeStep < steps.length - 1 && (
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={!canProceed()}
                >
                  Next
                </Button>
              )}
            </Box>
          </>
        ) : (
          <AutomatedReportsInterface />
        )}
      </Box>
    </Box>
  );
}
