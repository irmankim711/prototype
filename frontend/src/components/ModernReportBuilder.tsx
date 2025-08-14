import React, { useState, useCallback } from "react";
import {
  FileText,
  Eye,
  Download,
  Save,
  Plus,
  Trash2,
  BarChart3,
  Table,
  Image,
  Type,
  AlignLeft,
  List,
  Settings,
} from "lucide-react";
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  TextField,
  Divider,
  Chip,
  IconButton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import { styled } from "@mui/material/styles";

// Types for our content sections
interface SectionStyle {
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  lineHeight?: string;
  margin?: string;
  padding?: string;
  textAlign?: "left" | "center" | "right";
  backgroundColor?: string;
  borderRadius?: string;
  border?: string;
}

interface ChartData {
  type: "bar" | "line" | "pie";
  title: string;
  data: Array<{
    label: string;
    value: number;
    color?: string;
  }>;
}

interface TableData {
  headers: string[];
  rows: string[][];
  striped?: boolean;
  bordered?: boolean;
}

interface ListData {
  type: "bullet" | "numbered";
  items: string[];
}

interface ImageData {
  src: string;
  alt: string;
  caption?: string;
  width?: string;
  height?: string;
}

interface Section {
  id: string;
  type:
    | "heading"
    | "paragraph"
    | "chart"
    | "table"
    | "list"
    | "image"
    | "divider";
  content: string | ChartData | TableData | ListData | ImageData;
  style: SectionStyle;
  order: number;
}

interface ReportData {
  title: string;
  description?: string;
  author?: string;
  sections: Section[];
  theme: {
    primaryColor: string;
    secondaryColor: string;
    fontFamily: string;
  };
}

// Styled components
const StyledPaper = styled(Paper)(({ theme }) => ({
  borderRadius: 16,
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
  transition: "all 0.3s ease",
  "&:hover": {
    boxShadow: "0 12px 48px rgba(0, 0, 0, 0.15)",
  },
}));

const ComponentButton = styled(Button)(({ theme }) => ({
  width: "100%",
  justifyContent: "flex-start",
  padding: theme.spacing(2),
  marginBottom: theme.spacing(1),
  borderRadius: 12,
  textTransform: "none",
  "&:hover": {
    backgroundColor: theme.palette.primary.light + "20",
    transform: "translateX(4px)",
  },
  transition: "all 0.2s ease",
}));

const EditableSection = styled(Box)<{
  isActive: boolean;
  previewMode: boolean;
}>(({ theme, isActive, previewMode }) => ({
  position: "relative",
  borderRadius: 8,
  padding: theme.spacing(2),
  cursor: previewMode ? "default" : "pointer",
  border: isActive
    ? `2px solid ${theme.palette.primary.main}`
    : "2px solid transparent",
  backgroundColor: isActive
    ? theme.palette.primary.light + "10"
    : "transparent",
  transition: "all 0.2s ease",
  "&:hover": {
    backgroundColor: previewMode ? "transparent" : theme.palette.grey[50],
    border: previewMode
      ? "2px solid transparent"
      : `2px solid ${theme.palette.primary.light}`,
  },
}));

const ModernReportBuilder: React.FC = () => {
  const [reportData, setReportData] = useState<ReportData>({
    title: "Sample Report",
    description: "A comprehensive report built with our modern report builder",
    author: "Report Author",
    sections: [
      {
        id: "1",
        type: "heading",
        content: "Executive Summary",
        style: {
          fontSize: "32px",
          fontWeight: "bold",
          color: "#2563eb",
          margin: "20px 0",
        },
        order: 1,
      },
      {
        id: "2",
        type: "paragraph",
        content:
          "This report provides an overview of our quarterly performance metrics and key insights that drive our business forward.",
        style: { fontSize: "16px", lineHeight: "1.6", margin: "16px 0" },
        order: 2,
      },
      {
        id: "3",
        type: "chart",
        content: {
          type: "bar",
          title: "Quarterly Revenue Growth",
          data: [
            { label: "Q1 2024", value: 120000, color: "#3b82f6" },
            { label: "Q2 2024", value: 150000, color: "#10b981" },
            { label: "Q3 2024", value: 180000, color: "#f59e0b" },
            { label: "Q4 2024", value: 200000, color: "#ef4444" },
          ],
        } as ChartData,
        style: { margin: "24px 0" },
        order: 3,
      },
      {
        id: "4",
        type: "table",
        content: {
          headers: [
            "Department",
            "Budget",
            "Spent",
            "Remaining",
            "Utilization",
          ],
          rows: [
            ["Marketing", "$50,000", "$42,000", "$8,000", "84%"],
            ["Development", "$80,000", "$75,000", "$5,000", "94%"],
            ["Sales", "$60,000", "$55,000", "$5,000", "92%"],
            ["Operations", "$40,000", "$35,000", "$5,000", "88%"],
          ],
          striped: true,
          bordered: true,
        } as TableData,
        style: { margin: "24px 0" },
        order: 4,
      },
    ],
    theme: {
      primaryColor: "#2563eb",
      secondaryColor: "#10b981",
      fontFamily: "Inter, system-ui, sans-serif",
    },
  });

  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [styleDialogOpen, setStyleDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

  // Component renderers - Direct rendering without JSON
  const renderHeading = useCallback(
    (section: Section) => {
      const content = section.content as string;

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Typography
            component="h2"
            style={{
              ...section.style,
              fontFamily: reportData.theme.fontFamily,
            }}
          >
            {content}
          </Typography>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode, reportData.theme.fontFamily]
  );

  const renderParagraph = useCallback(
    (section: Section) => {
      const content = section.content as string;

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Typography
            component="p"
            style={{
              ...section.style,
              fontFamily: reportData.theme.fontFamily,
            }}
          >
            {content}
          </Typography>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode, reportData.theme.fontFamily]
  );

  const renderChart = useCallback(
    (section: Section) => {
      const chartData = section.content as ChartData;
      const maxValue = Math.max(...chartData.data.map((d) => d.value));

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Card sx={{ ...section.style, overflow: "visible" }}>
            <CardContent>
              <Typography
                variant="h6"
                component="h3"
                sx={{ mb: 3, textAlign: "center", fontWeight: 600 }}
              >
                {chartData.title}
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "end",
                  gap: 2,
                  height: 300,
                  p: 2,
                }}
              >
                {chartData.data.map((item, index) => (
                  <Box
                    key={index}
                    sx={{
                      flex: 1,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                    }}
                  >
                    <Box
                      sx={{
                        width: "100%",
                        backgroundColor:
                          item.color || reportData.theme.primaryColor,
                        borderRadius: "4px 4px 0 0",
                        transition: "all 0.3s ease",
                        height: `${(item.value / maxValue) * 250}px`,
                        minHeight: "20px",
                        display: "flex",
                        alignItems: "end",
                        justifyContent: "center",
                        color: "white",
                        fontWeight: "bold",
                        fontSize: "12px",
                        "&:hover": {
                          opacity: 0.8,
                          transform: "scale(1.02)",
                        },
                      }}
                    >
                      ${(item.value / 1000).toFixed(0)}K
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{ mt: 1, textAlign: "center", fontWeight: 500 }}
                    >
                      {item.label}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode, reportData.theme.primaryColor]
  );

  const renderTable = useCallback(
    (section: Section) => {
      const tableData = section.content as TableData;

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Box sx={{ ...section.style, overflow: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontFamily: reportData.theme.fontFamily,
              }}
            >
              <thead>
                <tr style={{ backgroundColor: reportData.theme.primaryColor }}>
                  {tableData.headers.map((header, index) => (
                    <th
                      key={index}
                      style={{
                        padding: "12px",
                        textAlign: "left",
                        fontWeight: 600,
                        color: "white",
                        border: tableData.bordered
                          ? "1px solid #e5e7eb"
                          : "none",
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableData.rows.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    style={{
                      backgroundColor:
                        tableData.striped && rowIndex % 2 === 1
                          ? "#f9fafb"
                          : "transparent",
                    }}
                  >
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        style={{
                          padding: "12px",
                          border: tableData.bordered
                            ? "1px solid #e5e7eb"
                            : "none",
                          borderTop: "1px solid #e5e7eb",
                        }}
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode, reportData.theme]
  );

  const renderList = useCallback(
    (section: Section) => {
      const listData = section.content as ListData;

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Box
            component={listData.type === "bullet" ? "ul" : "ol"}
            sx={section.style}
          >
            {listData.items.map((item, index) => (
              <li key={index} style={{ marginBottom: "8px", lineHeight: 1.6 }}>
                {item}
              </li>
            ))}
          </Box>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode]
  );

  const renderImage = useCallback(
    (section: Section) => {
      const imageData = section.content as ImageData;

      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Box sx={{ ...section.style, textAlign: "center" }}>
            <img
              src={imageData.src}
              alt={imageData.alt}
              style={{
                width: imageData.width || "auto",
                height: imageData.height || "auto",
                maxWidth: "100%",
                borderRadius: "8px",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
              }}
            />
            {imageData.caption && (
              <Typography
                variant="caption"
                sx={{ display: "block", mt: 1, fontStyle: "italic" }}
              >
                {imageData.caption}
              </Typography>
            )}
          </Box>
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode]
  );

  const renderDivider = useCallback(
    (section: Section) => {
      return (
        <EditableSection
          key={section.id}
          isActive={activeSection === section.id}
          previewMode={previewMode}
          onClick={() => !previewMode && setActiveSection(section.id)}
        >
          <Divider sx={{ ...section.style, my: 2 }} />
          {!previewMode && activeSection === section.id && (
            <Box sx={{ position: "absolute", top: 8, right: 8 }}>
              <IconButton
                size="small"
                onClick={() => deleteSection(section.id)}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          )}
        </EditableSection>
      );
    },
    [activeSection, previewMode]
  );

  // Content renderers map - Direct component rendering!
  const contentRenderers = {
    heading: renderHeading,
    paragraph: renderParagraph,
    chart: renderChart,
    table: renderTable,
    list: renderList,
    image: renderImage,
    divider: renderDivider,
  };

  // Section management functions
  const addSection = useCallback(
    (type: Section["type"]) => {
      const newSection: Section = {
        id: Date.now().toString(),
        type,
        content: getSectionDefaults(type),
        style: getDefaultStyles(type),
        order: reportData.sections.length + 1,
      };

      setReportData((prev) => ({
        ...prev,
        sections: [...prev.sections, newSection],
      }));

      setActiveSection(newSection.id);
    },
    [reportData.sections.length]
  );

  const getSectionDefaults = (type: Section["type"]) => {
    switch (type) {
      case "heading":
        return "New Heading";
      case "paragraph":
        return "Enter your text content here. Click to edit this paragraph and add your own content.";
      case "chart":
        return {
          type: "bar",
          title: "New Chart",
          data: [
            { label: "Category A", value: 100, color: "#3b82f6" },
            { label: "Category B", value: 120, color: "#10b981" },
            { label: "Category C", value: 140, color: "#f59e0b" },
          ],
        } as ChartData;
      case "table":
        return {
          headers: ["Column 1", "Column 2", "Column 3"],
          rows: [
            ["Data 1", "Data 2", "Data 3"],
            ["Data 4", "Data 5", "Data 6"],
          ],
          striped: true,
          bordered: true,
        } as TableData;
      case "list":
        return {
          type: "bullet",
          items: ["First item", "Second item", "Third item"],
        } as ListData;
      case "image":
        return {
          src: "https://via.placeholder.com/600x300?text=Sample+Image",
          alt: "Sample image",
          caption: "Sample image caption",
          width: "100%",
        } as ImageData;
      case "divider":
        return "";
      default:
        return "";
    }
  };

  const getDefaultStyles = (type: Section["type"]): SectionStyle => {
    switch (type) {
      case "heading":
        return {
          fontSize: "28px",
          fontWeight: "bold",
          color: reportData.theme.primaryColor,
          margin: "20px 0 10px 0",
        };
      case "paragraph":
        return {
          fontSize: "16px",
          lineHeight: "1.6",
          margin: "16px 0",
        };
      case "chart":
      case "table":
        return { margin: "24px 0" };
      case "list":
        return {
          fontSize: "16px",
          lineHeight: "1.6",
          margin: "16px 0",
          padding: "0 0 0 20px",
        };
      case "image":
        return { margin: "20px 0", textAlign: "center" };
      case "divider":
        return { margin: "32px 0" };
      default:
        return {};
    }
  };

  const updateSection = useCallback(
    (sectionId: string, updates: Partial<Section>) => {
      setReportData((prev) => ({
        ...prev,
        sections: prev.sections.map((section) =>
          section.id === sectionId ? { ...section, ...updates } : section
        ),
      }));
    },
    []
  );

  const deleteSection = useCallback((sectionId: string) => {
    setReportData((prev) => ({
      ...prev,
      sections: prev.sections.filter((section) => section.id !== sectionId),
    }));
    setActiveSection(null);
  }, []);

  const generatePreview = useCallback(() => {
    return reportData.sections
      .sort((a, b) => a.order - b.order)
      .map((section) => {
        const renderer = contentRenderers[section.type];
        return renderer ? renderer(section) : null;
      });
  }, [reportData.sections, contentRenderers]);

  const exportReport = useCallback((format: "pdf" | "docx" | "html") => {
    // Implementation for export functionality
    console.log(`Exporting report as ${format}`);
    setExportDialogOpen(false);
  }, []);

  const saveReport = useCallback(() => {
    // Implementation for save functionality
    console.log("Saving report", reportData);
  }, [reportData]);

  return (
    <Box sx={{ minHeight: "100vh", backgroundColor: "#f8fafc" }}>
      {/* Header */}
      <StyledPaper sx={{ borderRadius: 0, mb: 3 }}>
        <Box sx={{ p: 3 }}>
          <Grid container alignItems="center" justifyContent="space-between">
            <Grid item>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <FileText size={32} color="#2563eb" />
                <Box>
                  <Typography
                    variant="h4"
                    component="h1"
                    sx={{ fontWeight: 700, color: "#1e293b" }}
                  >
                    Modern Report Builder
                  </Typography>
                  <Typography variant="subtitle1" sx={{ color: "#64748b" }}>
                    Direct component rendering • No JSON overhead • Live preview
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item>
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant={previewMode ? "contained" : "outlined"}
                  startIcon={<Eye size={20} />}
                  onClick={() => setPreviewMode(!previewMode)}
                  sx={{ borderRadius: 2 }}
                >
                  {previewMode ? "Edit Mode" : "Preview"}
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Save size={20} />}
                  onClick={saveReport}
                  sx={{
                    borderRadius: 2,
                    bgcolor: "#10b981",
                    "&:hover": { bgcolor: "#059669" },
                  }}
                >
                  Save
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Download size={20} />}
                  onClick={() => setExportDialogOpen(true)}
                  sx={{
                    borderRadius: 2,
                    bgcolor: "#8b5cf6",
                    "&:hover": { bgcolor: "#7c3aed" },
                  }}
                >
                  Export
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </StyledPaper>

      <Grid container spacing={3} sx={{ px: 3 }}>
        {/* Sidebar - Component Library */}
        {!previewMode && (
          <Grid item xs={12} md={3}>
            <StyledPaper sx={{ p: 3, position: "sticky", top: 20 }}>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Components
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle2"
                  sx={{ mb: 2, color: "#64748b" }}
                >
                  Content
                </Typography>
                <ComponentButton
                  startIcon={<Type size={20} />}
                  onClick={() => addSection("heading")}
                  variant="outlined"
                >
                  Heading
                </ComponentButton>
                <ComponentButton
                  startIcon={<AlignLeft size={20} />}
                  onClick={() => addSection("paragraph")}
                  variant="outlined"
                >
                  Paragraph
                </ComponentButton>
                <ComponentButton
                  startIcon={<List size={20} />}
                  onClick={() => addSection("list")}
                  variant="outlined"
                >
                  List
                </ComponentButton>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle2"
                  sx={{ mb: 2, color: "#64748b" }}
                >
                  Data Visualization
                </Typography>
                <ComponentButton
                  startIcon={<BarChart3 size={20} />}
                  onClick={() => addSection("chart")}
                  variant="outlined"
                >
                  Chart
                </ComponentButton>
                <ComponentButton
                  startIcon={<Table size={20} />}
                  onClick={() => addSection("table")}
                  variant="outlined"
                >
                  Table
                </ComponentButton>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography
                  variant="subtitle2"
                  sx={{ mb: 2, color: "#64748b" }}
                >
                  Media & Layout
                </Typography>
                <ComponentButton
                  startIcon={<Image size={20} />}
                  onClick={() => addSection("image")}
                  variant="outlined"
                >
                  Image
                </ComponentButton>
                <ComponentButton
                  startIcon={
                    <div
                      style={{
                        width: 20,
                        height: 2,
                        backgroundColor: "currentColor",
                      }}
                    />
                  }
                  onClick={() => addSection("divider")}
                  variant="outlined"
                >
                  Divider
                </ComponentButton>
              </Box>

              {/* Section Properties */}
              {activeSection && (
                <Box sx={{ pt: 3, borderTop: 1, borderColor: "divider" }}>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    Properties
                  </Typography>
                  <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    startIcon={<Trash2 size={16} />}
                    onClick={() => deleteSection(activeSection)}
                    sx={{ mb: 1 }}
                  >
                    Delete Section
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Settings size={16} />}
                    onClick={() => setStyleDialogOpen(true)}
                  >
                    Style Options
                  </Button>
                </Box>
              )}
            </StyledPaper>
          </Grid>
        )}

        {/* Main Content - Live Preview */}
        <Grid item xs={12} md={previewMode ? 12 : 9}>
          <StyledPaper sx={{ p: 4, minHeight: "80vh" }}>
            {/* Report Header */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: 1, borderColor: "divider" }}>
              {previewMode ? (
                <>
                  <Typography
                    variant="h3"
                    component="h1"
                    sx={{ fontWeight: 700, mb: 1, color: "#1e293b" }}
                  >
                    {reportData.title}
                  </Typography>
                  {reportData.description && (
                    <Typography variant="h6" sx={{ color: "#64748b", mb: 2 }}>
                      {reportData.description}
                    </Typography>
                  )}
                  <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                    <Chip
                      label={`By ${reportData.author}`}
                      variant="outlined"
                    />
                    <Chip
                      label={`Generated on ${new Date().toLocaleDateString()}`}
                      variant="outlined"
                    />
                    <Chip
                      label={`${reportData.sections.length} sections`}
                      variant="outlined"
                    />
                  </Box>
                </>
              ) : (
                <Box>
                  <TextField
                    fullWidth
                    variant="outlined"
                    value={reportData.title}
                    onChange={(e) =>
                      setReportData((prev) => ({
                        ...prev,
                        title: e.target.value,
                      }))
                    }
                    sx={{
                      mb: 2,
                      "& .MuiOutlinedInput-root": {
                        fontSize: "2rem",
                        fontWeight: 700,
                      },
                    }}
                    placeholder="Enter report title..."
                  />
                  <TextField
                    fullWidth
                    variant="outlined"
                    value={reportData.description}
                    onChange={(e) =>
                      setReportData((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    sx={{ mb: 2 }}
                    placeholder="Enter report description..."
                  />
                  <TextField
                    fullWidth
                    variant="outlined"
                    value={reportData.author}
                    onChange={(e) =>
                      setReportData((prev) => ({
                        ...prev,
                        author: e.target.value,
                      }))
                    }
                    placeholder="Author name..."
                  />
                </Box>
              )}
            </Box>

            {/* Dynamic Content - Direct Component Rendering! */}
            <Box sx={{ minHeight: "400px" }}>
              {reportData.sections.length > 0 ? (
                <Box sx={{ "& > *": { mb: 2 } }}>{generatePreview()}</Box>
              ) : (
                <Box
                  sx={{
                    textAlign: "center",
                    py: 8,
                    color: "#64748b",
                    border: "2px dashed #cbd5e1",
                    borderRadius: 2,
                  }}
                >
                  <FileText
                    size={64}
                    style={{ marginBottom: 16, opacity: 0.5 }}
                  />
                  <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
                    Start Building Your Report
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 3 }}>
                    Add components from the sidebar to create your professional
                    report
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Plus size={20} />}
                    onClick={() => addSection("heading")}
                    sx={{ borderRadius: 2 }}
                  >
                    Add Your First Component
                  </Button>
                </Box>
              )}
            </Box>
          </StyledPaper>
        </Grid>
      </Grid>

      {/* Export Dialog */}
      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Export Report</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 3, color: "#64748b" }}>
            Choose your preferred export format
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => exportReport("pdf")}
                sx={{ p: 3, flexDirection: "column", height: 100 }}
              >
                <Download size={24} />
                <Typography variant="caption" sx={{ mt: 1 }}>
                  PDF
                </Typography>
              </Button>
            </Grid>
            <Grid item xs={4}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => exportReport("docx")}
                sx={{ p: 3, flexDirection: "column", height: 100 }}
              >
                <Download size={24} />
                <Typography variant="caption" sx={{ mt: 1 }}>
                  Word
                </Typography>
              </Button>
            </Grid>
            <Grid item xs={4}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => exportReport("html")}
                sx={{ p: 3, flexDirection: "column", height: 100 }}
              >
                <Download size={24} />
                <Typography variant="caption" sx={{ mt: 1 }}>
                  HTML
                </Typography>
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for Quick Add */}
      {!previewMode && (
        <Fab
          color="primary"
          sx={{ position: "fixed", bottom: 24, right: 24 }}
          onClick={() => addSection("paragraph")}
        >
          <Plus size={24} />
        </Fab>
      )}
    </Box>
  );
};

export default ModernReportBuilder;
