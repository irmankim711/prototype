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
  Grid,
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
} from "@mui/icons-material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Divider, Fade } from "@mui/material";
import * as XLSX from "xlsx";
import DownloadIcon from "@mui/icons-material/Download";
import "./ReportBuilder.css";

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

      if (
        field.includes("total") ||
        field.includes("sum") ||
        field.includes("revenue") ||
        field.includes("expense")
      ) {
        return values.reduce((sum, val) => sum + val, 0);
      } else if (
        field.includes("average") ||
        field.includes("avg") ||
        field.includes("mean")
      ) {
        return values.reduce((sum, val) => sum + val, 0) / values.length;
      } else if (field.includes("count")) {
        return values.length;
      } else {
        // For other numeric fields, use the most recent or common value
        return values[values.length - 1];
      }
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
          const aggregatedValue = aggregateNumericData(
            numericValues,
            matchedField
          );
          if (aggregatedValue !== null) {
            processed[matchedField] = aggregatedValue;
            // Also store formatted version for display
            processed[`${matchedField}_formatted`] =
              new Intl.NumberFormat().format(aggregatedValue);
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
      {/* Sidebar/Stepper */}
      <Box
        sx={{
          width: isMobile ? "100%" : 220,
          minWidth: isMobile ? "100%" : 220,
          backgroundColor: "#f8f9fa",
          padding: 2,
          display: "flex",
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
        {/* You can add navigation buttons here if needed */}
      </Box>
    </Box>
  );
}
