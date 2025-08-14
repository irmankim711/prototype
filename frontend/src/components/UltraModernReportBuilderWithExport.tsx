import React, { useState, useRef, useCallback, useMemo } from "react";
import {
  FileText,
  Eye,
  Download,
  Save,
  Plus,
  BarChart3,
  Table,
  Type,
  AlignLeft,
  Trash2,
  FileSpreadsheet,
  Upload,
  Settings,
  Zap,
  Database,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Palette,
  Layout,
  Moon,
  Sun,
} from "lucide-react";
import * as XLSX from "xlsx";

// Enhanced interfaces for XLSX integration
interface ExportOptions {
  format: "xlsx" | "csv" | "pdf" | "docx";
  includeCharts: boolean;
  includeFormatting: boolean;
  sheetName: string;
  autoColumnWidth: boolean;
}

interface DataSource {
  id: string;
  name: string;
  type: "excel" | "csv" | "api" | "database";
  url?: string;
  data?: any[];
  lastUpdated?: Date;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface AutomationRule {
  id: string;
  name: string;
  trigger: "schedule" | "data_change" | "manual";
  schedule?: string; // cron expression
  actions: string[];
  enabled: boolean;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  components: ComponentData[];
  dataSources: DataSource[];
  automationRules: AutomationRule[];
}

interface ComponentData {
  id: string;
  type: "heading" | "paragraph" | "chart" | "table" | "image" | "metric";
  content: any;
  style: ComponentStyle;
  dataSource?: string;
  position: { x: number; y: number };
}

interface ComponentStyle {
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  backgroundColor?: string;
  padding?: string;
  margin?: string;
  textAlign?: "left" | "center" | "right";
  borderRadius?: string;
  border?: string;
  boxShadow?: string;
}

// Modern Theme System
const themes = {
  light: {
    primary: "#3b82f6",
    secondary: "#6366f1",
    accent: "#8b5cf6",
    background: "#ffffff",
    surface: "#f8fafc",
    text: "#1e293b",
    textSecondary: "#64748b",
    border: "#e2e8f0",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
  },
  dark: {
    primary: "#60a5fa",
    secondary: "#818cf8",
    accent: "#a78bfa",
    background: "#0f172a",
    surface: "#1e293b",
    text: "#f8fafc",
    textSecondary: "#94a3b8",
    border: "#334155",
    success: "#34d399",
    warning: "#fbbf24",
    error: "#f87171",
  },
};

// Enhanced Component Library
const ModernHeading: React.FC<{
  content: string;
  level: 1 | 2 | 3 | 4 | 5 | 6;
  style: ComponentStyle;
  isEditing: boolean;
  isSelected: boolean;
  onChange: (content: string) => void;
  onSelect: () => void;
  onDelete: () => void;
  theme: typeof themes.light;
}> = ({
  content,
  level,
  style,
  isEditing,
  isSelected,
  onChange,
  onSelect,
  onDelete,
  theme,
}) => {
  const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements;

  const baseStyles = {
    h1: "text-4xl font-bold",
    h2: "text-3xl font-semibold",
    h3: "text-2xl font-medium",
    h4: "text-xl font-medium",
    h5: "text-lg font-medium",
    h6: "text-base font-medium",
  };

  if (isEditing) {
    return (
      <div className="relative group">
        <input
          type="text"
          value={content}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full bg-transparent outline-none border-2 border-blue-400 rounded-lg p-3 ${baseStyles[HeadingTag]}`}
          style={{
            color: style.color || theme.text,
            backgroundColor: style.backgroundColor || "transparent",
            ...style,
          }}
          placeholder="Enter heading..."
          autoFocus
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-200 rounded-lg p-3 ${
        isSelected
          ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20"
          : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
      }`}
    >
      <HeadingTag
        className={baseStyles[HeadingTag]}
        style={{
          color: style.color || theme.text,
          backgroundColor: style.backgroundColor || "transparent",
          ...style,
        }}
      >
        {content || "Empty Heading"}
      </HeadingTag>
    </div>
  );
};

const ModernParagraph: React.FC<{
  content: string;
  style: ComponentStyle;
  isEditing: boolean;
  isSelected: boolean;
  onChange: (content: string) => void;
  onSelect: () => void;
  onDelete: () => void;
  theme: typeof themes.light;
}> = ({
  content,
  style,
  isEditing,
  isSelected,
  onChange,
  onSelect,
  onDelete,
  theme,
}) => {
  if (isEditing) {
    return (
      <div className="relative group">
        <textarea
          value={content}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-transparent outline-none border-2 border-green-400 rounded-lg p-3 min-h-[100px] resize-none text-base leading-relaxed"
          style={{
            color: style.color || theme.text,
            backgroundColor: style.backgroundColor || "transparent",
            ...style,
          }}
          placeholder="Enter paragraph text..."
          autoFocus
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-200 rounded-lg p-3 ${
        isSelected
          ? "ring-2 ring-green-500 bg-green-50 dark:bg-green-900/20"
          : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
      }`}
    >
      <p
        className="text-base leading-relaxed"
        style={{
          color: style.color || theme.text,
          backgroundColor: style.backgroundColor || "transparent",
          ...style,
        }}
      >
        {content || "Empty paragraph"}
      </p>
    </div>
  );
};

const ModernChart: React.FC<{
  chartData: { title: string; data: Array<{ label: string; value: number }> };
  style: ComponentStyle;
  isEditing: boolean;
  isSelected: boolean;
  onChange: (data: any) => void;
  onSelect: () => void;
  onDelete: () => void;
  theme: typeof themes.light;
  dataSource?: DataSource;
}> = ({
  chartData,
  style,
  isEditing,
  isSelected,
  onChange,
  onSelect,
  onDelete,
  theme,
  dataSource,
}) => {
  const [localData, setLocalData] = useState(chartData);
  const colors = [
    theme.primary,
    theme.secondary,
    theme.accent,
    theme.success,
    theme.warning,
  ];

  const maxValue = Math.max(...localData.data.map((d) => d.value), 1);

  const updateTitle = (title: string) => {
    const newData = { ...localData, title };
    setLocalData(newData);
    onChange(newData);
  };

  if (isEditing) {
    return (
      <div className="relative group p-4 border-2 border-purple-400 rounded-lg bg-gradient-to-br from-white to-purple-50 dark:from-gray-900 dark:to-purple-900/20">
        <input
          type="text"
          value={localData.title}
          onChange={(e) => updateTitle(e.target.value)}
          className="text-xl font-semibold mb-4 w-full bg-transparent border-b border-gray-300 outline-none text-center"
          placeholder="Chart title..."
          style={{ color: theme.text }}
        />

        {dataSource && (
          <div className="mb-3 p-2 bg-blue-100 dark:bg-blue-900/30 rounded text-sm">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              <span>Data Source: {dataSource.name}</span>
              <RefreshCw className="w-4 h-4 cursor-pointer hover:animate-spin" />
            </div>
          </div>
        )}

        <div className="flex items-end space-x-2 h-40 bg-white dark:bg-gray-800 rounded p-4">
          {localData.data.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t transition-all duration-500 hover:opacity-80"
                style={{
                  height: `${(item.value / maxValue) * 120}px`,
                  backgroundColor: colors[index % colors.length],
                  minHeight: "10px",
                }}
              />
              <div className="mt-2 text-center">
                <div
                  className="text-xs font-medium"
                  style={{ color: theme.text }}
                >
                  {item.label}
                </div>
                <div className="text-xs" style={{ color: theme.textSecondary }}>
                  {item.value}
                </div>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-200 rounded-lg p-4 ${
        isSelected
          ? "ring-2 ring-purple-500 bg-purple-50 dark:bg-purple-900/20"
          : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
      }`}
    >
      <h3
        className="text-xl font-semibold text-center mb-4"
        style={{ color: theme.text }}
      >
        {localData.title}
      </h3>

      <div className="flex items-end space-x-2 h-40 bg-gradient-to-t from-gray-100 to-white dark:from-gray-800 dark:to-gray-700 rounded p-4">
        {localData.data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div
              className="w-full rounded-t transition-all duration-500 hover:opacity-80 shadow-sm"
              style={{
                height: `${(item.value / maxValue) * 120}px`,
                backgroundColor: colors[index % colors.length],
                minHeight: "10px",
              }}
            />
            <div className="mt-2 text-center">
              <div
                className="text-xs font-medium"
                style={{ color: theme.text }}
              >
                {item.label}
              </div>
              <div className="text-xs" style={{ color: theme.textSecondary }}>
                {item.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ModernTable: React.FC<{
  tableData: { headers: string[]; rows: string[][] };
  style: ComponentStyle;
  isEditing: boolean;
  isSelected: boolean;
  onChange: (data: any) => void;
  onSelect: () => void;
  onDelete: () => void;
  theme: typeof themes.light;
  dataSource?: DataSource;
}> = ({
  tableData,
  style,
  isEditing,
  isSelected,
  onChange,
  onSelect,
  onDelete,
  theme,
  dataSource,
}) => {
  if (isEditing) {
    return (
      <div className="relative group p-4 border-2 border-orange-400 rounded-lg bg-gradient-to-br from-white to-orange-50 dark:from-gray-900 dark:to-orange-900/20">
        {dataSource && (
          <div className="mb-3 p-2 bg-blue-100 dark:bg-blue-900/30 rounded text-sm">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              <span>Data Source: {dataSource.name}</span>
              <RefreshCw className="w-4 h-4 cursor-pointer hover:animate-spin" />
            </div>
          </div>
        )}

        <div className="overflow-auto max-h-64">
          <table className="w-full border-collapse rounded-lg overflow-hidden shadow-sm">
            <thead>
              <tr className="bg-gradient-to-r from-orange-500 to-orange-600">
                {tableData.headers.map((header, index) => (
                  <th
                    key={index}
                    className="border border-orange-300 p-3 text-left font-semibold text-white"
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
                  className={`${
                    rowIndex % 2 === 0
                      ? "bg-white dark:bg-gray-800"
                      : "bg-orange-50 dark:bg-gray-700"
                  } hover:bg-orange-100 dark:hover:bg-gray-600 transition-colors`}
                >
                  {row.map((cell, cellIndex) => (
                    <td
                      key={cellIndex}
                      className="border border-orange-200 dark:border-gray-600 p-3"
                      style={{ color: theme.text }}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-200 rounded-lg p-4 ${
        isSelected
          ? "ring-2 ring-orange-500 bg-orange-50 dark:bg-orange-900/20"
          : "hover:bg-gray-50 dark:hover:bg-gray-800/50"
      }`}
    >
      <div className="overflow-auto max-h-64">
        <table className="w-full border-collapse rounded-lg overflow-hidden shadow-sm">
          <thead>
            <tr className="bg-gradient-to-r from-orange-500 to-orange-600">
              {tableData.headers.map((header, index) => (
                <th
                  key={index}
                  className="border border-orange-300 p-3 text-left font-semibold text-white"
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
                className={`${
                  rowIndex % 2 === 0
                    ? "bg-white dark:bg-gray-800"
                    : "bg-orange-50 dark:bg-gray-700"
                } hover:bg-orange-100 dark:hover:bg-gray-600 transition-colors`}
              >
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="border border-orange-200 dark:border-gray-600 p-3"
                    style={{ color: theme.text }}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main Enhanced Report Builder with XLSX Export
const UltraModernReportBuilderWithExport: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [reportTitle, setReportTitle] = useState("Advanced Analytics Report");
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(
    null
  );
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [showExportPanel, setShowExportPanel] = useState(false);
  const [showDataSourcePanel, setShowDataSourcePanel] = useState(false);
  const [showAutomationPanel, setShowAutomationPanel] = useState(false);

  const theme = isDarkMode ? themes.dark : themes.light;
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Component state management
  const [components, setComponents] = useState<ComponentData[]>([
    {
      id: "1",
      type: "heading",
      content: "Executive Summary",
      style: { fontSize: "2rem", fontWeight: "bold", color: theme.primary },
      position: { x: 0, y: 0 },
    },
    {
      id: "2",
      type: "paragraph",
      content:
        "This comprehensive report provides detailed analytics and insights for strategic decision-making. The data has been analyzed across multiple dimensions to provide actionable recommendations.",
      style: { fontSize: "1rem", lineHeight: "1.6" },
      position: { x: 0, y: 1 },
    },
    {
      id: "3",
      type: "chart",
      content: {
        title: "Quarterly Performance Metrics",
        data: [
          { label: "Q1", value: 85 },
          { label: "Q2", value: 92 },
          { label: "Q3", value: 78 },
          { label: "Q4", value: 95 },
        ],
      },
      style: {},
      position: { x: 0, y: 2 },
    },
    {
      id: "4",
      type: "table",
      content: {
        headers: ["Department", "Budget", "Actual", "Variance", "Status"],
        rows: [
          ["Marketing", "$50,000", "$47,500", "-$2,500", "✅ On Track"],
          ["Development", "$80,000", "$82,000", "+$2,000", "⚠️ Over Budget"],
          ["Sales", "$60,000", "$58,500", "-$1,500", "✅ Under Budget"],
          ["Operations", "$40,000", "$39,000", "-$1,000", "✅ On Track"],
        ],
      },
      style: {},
      position: { x: 0, y: 3 },
    },
  ]);

  const [dataSources, setDataSources] = useState<DataSource[]>([
    {
      id: "ds1",
      name: "Sales Data 2024",
      type: "excel",
      lastUpdated: new Date(),
      autoRefresh: false,
    },
    {
      id: "ds2",
      name: "Financial Metrics",
      type: "api",
      url: "https://api.example.com/financial",
      lastUpdated: new Date(),
      autoRefresh: true,
      refreshInterval: 300000, // 5 minutes
    },
  ]);

  const [automationRules, setAutomationRules] = useState<AutomationRule[]>([
    {
      id: "ar1",
      name: "Daily Report Generation",
      trigger: "schedule",
      schedule: "0 9 * * *", // 9 AM daily
      actions: ["generate_report", "send_email"],
      enabled: true,
    },
  ]);

  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: "xlsx",
    includeCharts: true,
    includeFormatting: true,
    sheetName: "Analytics Report",
    autoColumnWidth: true,
  });

  // XLSX Export Functions
  const exportToXLSX = useCallback(() => {
    try {
      // Create a new workbook
      const wb = XLSX.utils.book_new();

      // Create main data sheet
      const wsData: any[][] = [];

      // Add report title
      wsData.push([reportTitle]);
      wsData.push([]); // Empty row

      // Process each component
      components.forEach((component, index) => {
        switch (component.type) {
          case "heading":
            wsData.push([`HEADING: ${component.content}`]);
            wsData.push([]);
            break;

          case "paragraph":
            wsData.push([`TEXT: ${component.content}`]);
            wsData.push([]);
            break;

          case "table":
            wsData.push([`TABLE: ${component.content.headers.join(" | ")}`]);
            wsData.push(component.content.headers);
            component.content.rows.forEach((row: string[]) => {
              wsData.push(row);
            });
            wsData.push([]);
            break;

          case "chart":
            wsData.push([`CHART: ${component.content.title}`]);
            wsData.push(["Label", "Value"]);
            component.content.data.forEach((item: any) => {
              wsData.push([item.label, item.value]);
            });
            wsData.push([]);
            break;
        }
      });

      // Create worksheet
      const ws = XLSX.utils.aoa_to_sheet(wsData);

      // Auto-size columns if enabled
      if (exportOptions.autoColumnWidth) {
        const colWidths = wsData.reduce((acc, row) => {
          row.forEach((cell, i) => {
            const cellLength = String(cell || "").length;
            acc[i] = Math.max(acc[i] || 10, cellLength + 2);
          });
          return acc;
        }, {} as Record<number, number>);

        ws["!cols"] = Object.keys(colWidths).map((i) => ({
          width: colWidths[parseInt(i)],
        }));
      }

      // Add styling if enabled
      if (exportOptions.includeFormatting) {
        // Add basic styling (XLSX-js has limited styling support)
        ws["!margins"] = {
          left: 0.7,
          right: 0.7,
          top: 0.75,
          bottom: 0.75,
          header: 0.3,
          footer: 0.3,
        };
      }

      XLSX.utils.book_append_sheet(wb, ws, exportOptions.sheetName);

      // Create summary sheet
      const summaryData = [
        ["Report Summary"],
        [],
        ["Report Title", reportTitle],
        ["Generated On", new Date().toLocaleString()],
        ["Total Components", components.length.toString()],
        ["Data Sources", dataSources.length.toString()],
        ["Automation Rules", automationRules.length.toString()],
        [],
        ["Component Breakdown"],
        ["Type", "Count"],
        [
          "Headings",
          components.filter((c) => c.type === "heading").length.toString(),
        ],
        [
          "Paragraphs",
          components.filter((c) => c.type === "paragraph").length.toString(),
        ],
        [
          "Charts",
          components.filter((c) => c.type === "chart").length.toString(),
        ],
        [
          "Tables",
          components.filter((c) => c.type === "table").length.toString(),
        ],
      ];

      const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
      XLSX.utils.book_append_sheet(wb, wsSummary, "Summary");

      // Generate and download file
      const fileName = `${reportTitle.replace(/[^a-z0-9]/gi, "_")}_${
        new Date().toISOString().split("T")[0]
      }.xlsx`;
      XLSX.writeFile(wb, fileName);

      // Show success message
      alert(`Successfully exported report as ${fileName}`);
    } catch (error) {
      console.error("Export error:", error);
      alert("Failed to export report. Please try again.");
    }
  }, [components, reportTitle, dataSources, automationRules, exportOptions]);

  // Import XLSX file and parse data
  const importFromXLSX = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: "array" });

          // Parse first sheet
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

          // Convert parsed data to components
          const newComponents: ComponentData[] = [];
          let componentId = Date.now();

          (jsonData as any[][]).forEach((row, index) => {
            if (row.length === 0) return;

            const firstCell = String(row[0] || "").trim();

            if (firstCell.startsWith("HEADING:")) {
              newComponents.push({
                id: (++componentId).toString(),
                type: "heading",
                content: firstCell.replace("HEADING:", "").trim(),
                style: {
                  fontSize: "2rem",
                  fontWeight: "bold",
                  color: theme.primary,
                },
                position: { x: 0, y: newComponents.length },
              });
            } else if (firstCell.startsWith("TEXT:")) {
              newComponents.push({
                id: (++componentId).toString(),
                type: "paragraph",
                content: firstCell.replace("TEXT:", "").trim(),
                style: { fontSize: "1rem", lineHeight: "1.6" },
                position: { x: 0, y: newComponents.length },
              });
            } else if (firstCell.startsWith("CHART:")) {
              // Look for chart data in following rows
              const chartTitle = firstCell.replace("CHART:", "").trim();
              const chartData: Array<{ label: string; value: number }> = [];

              for (let i = index + 2; i < (jsonData as any[][]).length; i++) {
                const dataRow = (jsonData as any[][])[i];
                if (!dataRow || dataRow.length < 2 || dataRow[0] === "") break;

                chartData.push({
                  label: String(dataRow[0]),
                  value: Number(dataRow[1]) || 0,
                });
              }

              newComponents.push({
                id: (++componentId).toString(),
                type: "chart",
                content: { title: chartTitle, data: chartData },
                style: {},
                position: { x: 0, y: newComponents.length },
              });
            } else if (firstCell.startsWith("TABLE:")) {
              // Look for table data in following rows
              const headers: string[] = [];
              const tableRows: string[][] = [];

              for (let i = index + 1; i < (jsonData as any[][]).length; i++) {
                const dataRow = (jsonData as any[][])[i];
                if (!dataRow || dataRow.length === 0) break;

                if (headers.length === 0) {
                  headers.push(...dataRow.map((cell) => String(cell || "")));
                } else {
                  tableRows.push(dataRow.map((cell) => String(cell || "")));
                }
              }

              newComponents.push({
                id: (++componentId).toString(),
                type: "table",
                content: { headers, rows: tableRows },
                style: {},
                position: { x: 0, y: newComponents.length },
              });
            }
          });

          if (newComponents.length > 0) {
            setComponents(newComponents);
            alert(
              `Successfully imported ${newComponents.length} components from Excel file!`
            );
          } else {
            alert("No valid components found in the Excel file.");
          }
        } catch (error) {
          console.error("Import error:", error);
          alert("Failed to import Excel file. Please check the file format.");
        }
      };
      reader.readAsArrayBuffer(file);
    },
    [theme.primary]
  );

  // Component management functions
  const addComponent = useCallback(
    (type: ComponentData["type"]) => {
      const newComponent: ComponentData = {
        id: Date.now().toString(),
        type,
        content: getDefaultContent(type),
        style: getDefaultStyle(type),
        position: { x: 0, y: components.length },
      };

      setComponents((prev) => [...prev, newComponent]);
      setSelectedComponent(newComponent.id);
      setEditingComponent(newComponent.id);
    },
    [components.length]
  );

  const getDefaultContent = (type: ComponentData["type"]) => {
    switch (type) {
      case "heading":
        return "New Heading";
      case "paragraph":
        return "Enter your paragraph content here...";
      case "chart":
        return {
          title: "New Chart",
          data: [
            { label: "Item 1", value: 25 },
            { label: "Item 2", value: 50 },
            { label: "Item 3", value: 75 },
          ],
        };
      case "table":
        return {
          headers: ["Column 1", "Column 2", "Column 3"],
          rows: [
            ["Data 1", "Data 2", "Data 3"],
            ["Data 4", "Data 5", "Data 6"],
          ],
        };
      default:
        return "";
    }
  };

  const getDefaultStyle = (type: ComponentData["type"]): ComponentStyle => {
    switch (type) {
      case "heading":
        return { fontSize: "2rem", fontWeight: "bold", color: theme.primary };
      case "paragraph":
        return { fontSize: "1rem", lineHeight: "1.6", color: theme.text };
      default:
        return {};
    }
  };

  const updateComponent = useCallback(
    (id: string, updates: Partial<ComponentData>) => {
      setComponents((prev) =>
        prev.map((component) =>
          component.id === id ? { ...component, ...updates } : component
        )
      );
    },
    []
  );

  const deleteComponent = useCallback(
    (id: string) => {
      setComponents((prev) => prev.filter((component) => component.id !== id));
      if (selectedComponent === id) setSelectedComponent(null);
      if (editingComponent === id) setEditingComponent(null);
    },
    [selectedComponent, editingComponent]
  );

  // Automation functions
  const triggerAutomation = useCallback(
    (ruleId: string) => {
      const rule = automationRules.find((r) => r.id === ruleId);
      if (!rule || !rule.enabled) return;

      alert(
        `Automation "${rule.name}" triggered! Actions: ${rule.actions.join(
          ", "
        )}`
      );

      // Simulate automation actions
      if (rule.actions.includes("generate_report")) {
        exportToXLSX();
      }
      if (rule.actions.includes("send_email")) {
        alert("Email sent to stakeholders!");
      }
    },
    [automationRules, exportToXLSX]
  );

  const renderComponent = useCallback(
    (component: ComponentData) => {
      const isSelected = selectedComponent === component.id;
      const isEditing = editingComponent === component.id;
      const dataSource = dataSources.find(
        (ds) => ds.id === component.dataSource
      );

      const commonProps = {
        isEditing,
        isSelected,
        onSelect: () => setSelectedComponent(component.id),
        onDelete: () => deleteComponent(component.id),
        theme,
        dataSource,
      };

      switch (component.type) {
        case "heading":
          return (
            <ModernHeading
              key={component.id}
              content={component.content}
              level={2}
              style={component.style}
              onChange={(content) => updateComponent(component.id, { content })}
              {...commonProps}
            />
          );
        case "paragraph":
          return (
            <ModernParagraph
              key={component.id}
              content={component.content}
              style={component.style}
              onChange={(content) => updateComponent(component.id, { content })}
              {...commonProps}
            />
          );
        case "chart":
          return (
            <ModernChart
              key={component.id}
              chartData={component.content}
              style={component.style}
              onChange={(content) => updateComponent(component.id, { content })}
              {...commonProps}
            />
          );
        case "table":
          return (
            <ModernTable
              key={component.id}
              tableData={component.content}
              style={component.style}
              onChange={(content) => updateComponent(component.id, { content })}
              {...commonProps}
            />
          );
        default:
          return null;
      }
    },
    [
      selectedComponent,
      editingComponent,
      theme,
      dataSources,
      updateComponent,
      deleteComponent,
    ]
  );

  return (
    <div
      className={`min-h-screen transition-all duration-300 ${
        isDarkMode ? "dark bg-gray-900" : "bg-gray-50"
      }`}
    >
      {/* Enhanced Header */}
      <div
        className={`${
          isDarkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-gray-200"
        } shadow-lg border-b backdrop-blur-sm bg-opacity-95`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1
                  className={`text-2xl font-bold ${
                    isDarkMode ? "text-white" : "text-gray-900"
                  }`}
                >
                  Ultra-Modern Report Builder
                </h1>
                <p
                  className={`text-sm ${
                    isDarkMode ? "text-gray-400" : "text-gray-600"
                  }`}
                >
                  AI-Powered • XLSX Export • Automation Ready
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {/* Theme Toggle */}
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode
                    ? "bg-gray-700 text-yellow-400 hover:bg-gray-600"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {isDarkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>

              {/* Preview Mode Toggle */}
              <button
                onClick={() => {
                  setIsPreviewMode(!isPreviewMode);
                  setEditingComponent(null);
                }}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-all ${
                  isPreviewMode
                    ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300"
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>{isPreviewMode ? "Edit Mode" : "Preview"}</span>
              </button>

              {/* Data Sources */}
              <button
                onClick={() => setShowDataSourcePanel(!showDataSourcePanel)}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  showDataSourcePanel
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300"
                }`}
              >
                <Database className="w-4 h-4" />
                <span>Data</span>
              </button>

              {/* Automation */}
              <button
                onClick={() => setShowAutomationPanel(!showAutomationPanel)}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  showAutomationPanel
                    ? "bg-purple-500 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300"
                }`}
              >
                <Zap className="w-4 h-4" />
                <span>Automation</span>
              </button>

              {/* Export Panel */}
              <button
                onClick={() => setShowExportPanel(!showExportPanel)}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  showExportPanel
                    ? "bg-orange-500 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300"
                }`}
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Export</span>
              </button>

              {/* Quick Export */}
              <button
                onClick={exportToXLSX}
                className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-lg flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Quick Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Export Panel */}
      {showExportPanel && (
        <div
          className={`${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          } border-b p-4`}
        >
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label
                  className={`block text-sm font-medium mb-2 ${
                    isDarkMode ? "text-gray-300" : "text-gray-700"
                  }`}
                >
                  Export Format
                </label>
                <select
                  value={exportOptions.format}
                  onChange={(e) =>
                    setExportOptions((prev) => ({
                      ...prev,
                      format: e.target.value as any,
                    }))
                  }
                  className={`w-full p-2 border rounded-lg ${
                    isDarkMode
                      ? "bg-gray-700 border-gray-600 text-white"
                      : "bg-white border-gray-300"
                  }`}
                >
                  <option value="xlsx">Excel (.xlsx)</option>
                  <option value="csv">CSV (.csv)</option>
                  <option value="pdf">PDF (.pdf)</option>
                  <option value="docx">Word (.docx)</option>
                </select>
              </div>

              <div>
                <label
                  className={`block text-sm font-medium mb-2 ${
                    isDarkMode ? "text-gray-300" : "text-gray-700"
                  }`}
                >
                  Sheet Name
                </label>
                <input
                  type="text"
                  value={exportOptions.sheetName}
                  onChange={(e) =>
                    setExportOptions((prev) => ({
                      ...prev,
                      sheetName: e.target.value,
                    }))
                  }
                  className={`w-full p-2 border rounded-lg ${
                    isDarkMode
                      ? "bg-gray-700 border-gray-600 text-white"
                      : "bg-white border-gray-300"
                  }`}
                />
              </div>

              <div className="flex flex-col space-y-2">
                <label
                  className={`block text-sm font-medium ${
                    isDarkMode ? "text-gray-300" : "text-gray-700"
                  }`}
                >
                  Options
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeCharts}
                    onChange={(e) =>
                      setExportOptions((prev) => ({
                        ...prev,
                        includeCharts: e.target.checked,
                      }))
                    }
                    className="rounded"
                  />
                  <span
                    className={`text-sm ${
                      isDarkMode ? "text-gray-300" : "text-gray-700"
                    }`}
                  >
                    Include Charts
                  </span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={exportOptions.autoColumnWidth}
                    onChange={(e) =>
                      setExportOptions((prev) => ({
                        ...prev,
                        autoColumnWidth: e.target.checked,
                      }))
                    }
                    className="rounded"
                  />
                  <span
                    className={`text-sm ${
                      isDarkMode ? "text-gray-300" : "text-gray-700"
                    }`}
                  >
                    Auto Column Width
                  </span>
                </label>
              </div>

              <div className="flex items-end space-x-2">
                <button
                  onClick={exportToXLSX}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all"
                >
                  Export Now
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) importFromXLSX(file);
                  }}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all"
                >
                  <Upload className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Sources Panel */}
      {showDataSourcePanel && (
        <div
          className={`${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          } border-b p-4`}
        >
          <div className="max-w-7xl mx-auto">
            <h3
              className={`font-semibold mb-3 ${
                isDarkMode ? "text-white" : "text-gray-900"
              }`}
            >
              Data Sources
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {dataSources.map((source) => (
                <div
                  key={source.id}
                  className={`p-4 rounded-lg border ${
                    isDarkMode
                      ? "bg-gray-700 border-gray-600"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4
                      className={`font-medium ${
                        isDarkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {source.name}
                    </h4>
                    <div
                      className={`px-2 py-1 rounded text-xs ${
                        source.type === "excel"
                          ? "bg-green-100 text-green-800"
                          : source.type === "api"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {source.type.toUpperCase()}
                    </div>
                  </div>
                  <div
                    className={`text-sm ${
                      isDarkMode ? "text-gray-300" : "text-gray-600"
                    }`}
                  >
                    Last updated: {source.lastUpdated?.toLocaleString()}
                  </div>
                  <div className="flex items-center mt-3 space-x-2">
                    <RefreshCw className="w-4 h-4 cursor-pointer hover:animate-spin" />
                    {source.autoRefresh && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Automation Panel */}
      {showAutomationPanel && (
        <div
          className={`${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          } border-b p-4`}
        >
          <div className="max-w-7xl mx-auto">
            <h3
              className={`font-semibold mb-3 ${
                isDarkMode ? "text-white" : "text-gray-900"
              }`}
            >
              Automation Rules
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {automationRules.map((rule) => (
                <div
                  key={rule.id}
                  className={`p-4 rounded-lg border ${
                    isDarkMode
                      ? "bg-gray-700 border-gray-600"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4
                      className={`font-medium ${
                        isDarkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {rule.name}
                    </h4>
                    <div
                      className={`px-2 py-1 rounded text-xs ${
                        rule.enabled
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {rule.enabled ? "Active" : "Disabled"}
                    </div>
                  </div>
                  <div
                    className={`text-sm ${
                      isDarkMode ? "text-gray-300" : "text-gray-600"
                    } mb-3`}
                  >
                    Trigger: {rule.trigger}{" "}
                    {rule.schedule && `(${rule.schedule})`}
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => triggerAutomation(rule.id)}
                      className="px-3 py-1 bg-purple-500 text-white rounded text-sm hover:bg-purple-600 transition-colors"
                    >
                      Run Now
                    </button>
                    <Clock className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Enhanced Sidebar */}
          {!isPreviewMode && (
            <div className="col-span-3">
              <div
                className={`${
                  isDarkMode
                    ? "bg-gray-800 border-gray-700"
                    : "bg-white border-gray-200"
                } rounded-xl shadow-xl border backdrop-blur-sm bg-opacity-95 sticky top-6`}
              >
                <div className="p-6">
                  <h3
                    className={`text-lg font-semibold mb-4 ${
                      isDarkMode ? "text-white" : "text-gray-900"
                    }`}
                  >
                    Component Library
                  </h3>

                  <div className="space-y-3">
                    <button
                      onClick={() => addComponent("heading")}
                      className={`w-full p-4 text-left border-2 rounded-xl hover:scale-105 transition-all duration-200 ${
                        isDarkMode
                          ? "border-gray-600 hover:border-blue-500 bg-gray-700 hover:bg-gray-600"
                          : "border-gray-200 hover:border-blue-300 bg-gradient-to-r from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-blue-500 text-white">
                          <Type className="w-5 h-5" />
                        </div>
                        <div>
                          <div
                            className={`font-medium ${
                              isDarkMode ? "text-white" : "text-gray-900"
                            }`}
                          >
                            Heading
                          </div>
                          <div
                            className={`text-sm ${
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }`}
                          >
                            Add title or section header
                          </div>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => addComponent("paragraph")}
                      className={`w-full p-4 text-left border-2 rounded-xl hover:scale-105 transition-all duration-200 ${
                        isDarkMode
                          ? "border-gray-600 hover:border-green-500 bg-gray-700 hover:bg-gray-600"
                          : "border-gray-200 hover:border-green-300 bg-gradient-to-r from-green-50 to-green-100 hover:from-green-100 hover:to-green-200"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-green-500 text-white">
                          <AlignLeft className="w-5 h-5" />
                        </div>
                        <div>
                          <div
                            className={`font-medium ${
                              isDarkMode ? "text-white" : "text-gray-900"
                            }`}
                          >
                            Paragraph
                          </div>
                          <div
                            className={`text-sm ${
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }`}
                          >
                            Add text content
                          </div>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => addComponent("chart")}
                      className={`w-full p-4 text-left border-2 rounded-xl hover:scale-105 transition-all duration-200 ${
                        isDarkMode
                          ? "border-gray-600 hover:border-purple-500 bg-gray-700 hover:bg-gray-600"
                          : "border-gray-200 hover:border-purple-300 bg-gradient-to-r from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-purple-500 text-white">
                          <BarChart3 className="w-5 h-5" />
                        </div>
                        <div>
                          <div
                            className={`font-medium ${
                              isDarkMode ? "text-white" : "text-gray-900"
                            }`}
                          >
                            Chart
                          </div>
                          <div
                            className={`text-sm ${
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }`}
                          >
                            Interactive data visualization
                          </div>
                        </div>
                      </div>
                    </button>

                    <button
                      onClick={() => addComponent("table")}
                      className={`w-full p-4 text-left border-2 rounded-xl hover:scale-105 transition-all duration-200 ${
                        isDarkMode
                          ? "border-gray-600 hover:border-orange-500 bg-gray-700 hover:bg-gray-600"
                          : "border-gray-200 hover:border-orange-300 bg-gradient-to-r from-orange-50 to-orange-100 hover:from-orange-100 hover:to-orange-200"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-orange-500 text-white">
                          <Table className="w-5 h-5" />
                        </div>
                        <div>
                          <div
                            className={`font-medium ${
                              isDarkMode ? "text-white" : "text-gray-900"
                            }`}
                          >
                            Table
                          </div>
                          <div
                            className={`text-sm ${
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }`}
                          >
                            Structured data display
                          </div>
                        </div>
                      </div>
                    </button>
                  </div>

                  {selectedComponent && (
                    <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
                      <h4
                        className={`font-semibold mb-3 ${
                          isDarkMode ? "text-white" : "text-gray-900"
                        }`}
                      >
                        Component Actions
                      </h4>
                      <div className="space-y-2">
                        <button
                          onClick={() =>
                            setEditingComponent(
                              editingComponent === selectedComponent
                                ? null
                                : selectedComponent
                            )
                          }
                          className={`w-full p-2 rounded-lg flex items-center space-x-2 transition-colors ${
                            editingComponent === selectedComponent
                              ? "bg-blue-500 text-white"
                              : isDarkMode
                              ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                          }`}
                        >
                          <Settings className="w-4 h-4" />
                          <span>
                            {editingComponent === selectedComponent
                              ? "Stop Editing"
                              : "Edit Component"}
                          </span>
                        </button>

                        <button
                          onClick={() => deleteComponent(selectedComponent)}
                          className="w-full p-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center space-x-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Delete Component</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Enhanced Main Content Area */}
          <div className={isPreviewMode ? "col-span-12" : "col-span-9"}>
            <div
              className={`${
                isDarkMode
                  ? "bg-gray-800 border-gray-700"
                  : "bg-white border-gray-200"
              } rounded-xl shadow-xl border backdrop-blur-sm bg-opacity-95`}
            >
              <div className="p-8">
                {/* Report Title */}
                <div className="mb-8">
                  {isPreviewMode ? (
                    <div>
                      <h1
                        className={`text-4xl font-bold mb-2 ${
                          isDarkMode ? "text-white" : "text-gray-900"
                        }`}
                      >
                        {reportTitle}
                      </h1>
                      <div
                        className={`text-sm ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        } flex items-center space-x-4`}
                      >
                        <span>
                          Generated on {new Date().toLocaleDateString()}
                        </span>
                        <span>•</span>
                        <span>{components.length} components</span>
                        <span>•</span>
                        <span>{dataSources.length} data sources</span>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <input
                        type="text"
                        value={reportTitle}
                        onChange={(e) => setReportTitle(e.target.value)}
                        className={`text-4xl font-bold mb-2 w-full bg-transparent border-b-2 border-blue-300 outline-none pb-2 ${
                          isDarkMode ? "text-white" : "text-gray-900"
                        }`}
                        placeholder="Enter report title..."
                      />
                      <div
                        className={`text-sm ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        } flex items-center space-x-4`}
                      >
                        <span>
                          Last edited {new Date().toLocaleDateString()}
                        </span>
                        <span>•</span>
                        <span>{components.length} components</span>
                        <span>•</span>
                        <span>Auto-save enabled</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Dynamic Components */}
                <div className="space-y-6">
                  {components.map(renderComponent)}
                </div>

                {/* Empty State */}
                {components.length === 0 && (
                  <div className="text-center py-16">
                    <div className="mb-6">
                      <div className="mx-auto w-24 h-24 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                        <Sparkles className="w-12 h-12 text-white" />
                      </div>
                    </div>
                    <h3
                      className={`text-2xl font-bold mb-2 ${
                        isDarkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      Create Your First Report
                    </h3>
                    <p
                      className={`${
                        isDarkMode ? "text-gray-400" : "text-gray-600"
                      } max-w-md mx-auto`}
                    >
                      Start building your professional report by adding
                      components from the sidebar. Export to Excel, automate
                      generation, and connect live data sources.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UltraModernReportBuilderWithExport;
