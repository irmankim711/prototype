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
  Move,
  Settings,
  Copy,
  Palette,
  ImageIcon,
  ListIcon,
  Sparkles,
  Layers,
  ChevronUp,
  ChevronDown,
  EyeOff,
  ZoomIn,
  ZoomOut,
  Grid,
  Layout,
  PaintBucket,
  Sun,
  Moon,
} from "lucide-react";

// Enhanced TypeScript interfaces
interface BaseComponentProps {
  id: string;
  isEditing?: boolean;
  isSelected?: boolean;
  onEdit?: (data: any) => void;
  onDelete?: () => void;
  onSelect?: () => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onDuplicate?: () => void;
  style?: ComponentStyle;
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
  opacity?: number;
}

interface ComponentData {
  id: string;
  type: "heading" | "paragraph" | "chart" | "table" | "image" | "list";
  content: any;
  style: ComponentStyle;
  isVisible: boolean;
}

// Enhanced Interactive Heading Component
const InteractiveHeading: React.FC<
  BaseComponentProps & {
    content: string;
    level: 1 | 2 | 3;
  }
> = ({
  _id,
  content,
  level,
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [text, setText] = useState(content);
  const [headingLevel, setHeadingLevel] = useState(level);

  const HeadingTag = `h${headingLevel}` as keyof JSX.IntrinsicElements;

  const defaultStyles = useMemo(
    () => ({
      h1: "text-4xl font-bold",
      h2: "text-3xl font-semibold",
      h3: "text-2xl font-medium",
    }),
    []
  );

  const handleEdit = useCallback(
    (newText: string) => {
      setText(newText);
      onEdit?.({ content: newText, level: headingLevel });
    },
    [onEdit, headingLevel]
  );

  if (isEditing) {
    return (
      <div
        className={`relative group p-4 border-2 rounded-lg transition-all ${
          isSelected
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-blue-400"
        }`}
      >
        {/* Editing Controls */}
        <div className="flex items-center gap-2 mb-3 text-sm">
          <select
            value={headingLevel}
            onChange={(e) =>
              setHeadingLevel(Number(e.target.value) as 1 | 2 | 3)
            }
            className="px-2 py-1 border rounded text-xs"
          >
            <option value={1}>H1 - Title</option>
            <option value={2}>H2 - Section</option>
            <option value={3}>H3 - Subsection</option>
          </select>
          <span className="text-gray-500">|</span>
          <button
            onClick={onDuplicate}
            className="px-2 py-1 bg-blue-100 rounded hover:bg-blue-200"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 bg-red-100 rounded hover:bg-red-200"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>

        <input
          type="text"
          value={text}
          onChange={(e) => handleEdit(e.target.value)}
          className={`${
            defaultStyles[`h${headingLevel}` as keyof typeof defaultStyles]
          } w-full bg-transparent border-none outline-none text-blue-600`}
          placeholder={`Enter ${HeadingTag.toUpperCase()} heading...`}
          style={style}
        />
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all rounded p-2 ${
        isSelected ? "ring-2 ring-blue-500 bg-blue-50" : "hover:bg-gray-50"
      }`}
    >
      <HeadingTag
        className={`${
          defaultStyles[`h${headingLevel}` as keyof typeof defaultStyles]
        } text-gray-800`}
        style={style}
      >
        {text}
      </HeadingTag>
    </div>
  );
};

// Enhanced Interactive Paragraph Component
const InteractiveParagraph: React.FC<
  BaseComponentProps & { content: string }
> = ({
  _id,
  content,
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [text, setText] = useState(content);

  const handleEdit = useCallback(
    (newText: string) => {
      setText(newText);
      onEdit?.({ content: newText });
    },
    [onEdit]
  );

  if (isEditing) {
    return (
      <div
        className={`relative group p-4 border-2 rounded-lg transition-all ${
          isSelected
            ? "border-green-500 bg-green-50"
            : "border-gray-300 hover:border-green-400"
        }`}
      >
        {/* Editing Controls */}
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-green-600 font-medium">Paragraph</span>
          <span className="text-gray-500">|</span>
          <button
            onClick={onDuplicate}
            className="px-2 py-1 bg-green-100 rounded hover:bg-green-200"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 bg-red-100 rounded hover:bg-red-200"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>

        <textarea
          value={text}
          onChange={(e) => handleEdit(e.target.value)}
          className="w-full bg-transparent border-none outline-none resize-none text-gray-700 leading-relaxed"
          rows={4}
          placeholder="Enter paragraph content..."
          style={style}
        />
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all rounded p-2 ${
        isSelected ? "ring-2 ring-green-500 bg-green-50" : "hover:bg-gray-50"
      }`}
    >
      <p className="text-gray-700 leading-relaxed" style={style}>
        {text}
      </p>
    </div>
  );
};

// Enhanced Interactive Chart Component
const InteractiveChart: React.FC<
  BaseComponentProps & {
    content: {
      title: string;
      data: Array<{ label: string; value: number; color?: string }>;
    };
  }
> = ({
  _id,
  content,
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [chartData, setChartData] = useState(content);
  const [chartType, setChartType] = useState<"bar" | "line" | "pie">("bar");

  const maxValue = useMemo(
    () => Math.max(...chartData.data.map((d) => d.value)),
    [chartData.data]
  );

  const handleTitleEdit = useCallback(
    (newTitle: string) => {
      const newData = { ...chartData, title: newTitle };
      setChartData(newData);
      onEdit?.(newData);
    },
    [chartData, onEdit]
  );

  const colors = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#06B6D4",
  ];

  if (isEditing) {
    return (
      <div
        className={`relative group p-4 border-2 rounded-lg transition-all ${
          isSelected
            ? "border-purple-500 bg-purple-50"
            : "border-gray-300 hover:border-purple-400"
        }`}
        style={style}
      >
        {/* Editing Controls */}
        <div className="flex items-center gap-2 mb-3 text-sm">
          <select
            value={chartType}
            onChange={(e) =>
              setChartType(e.target.value as "bar" | "line" | "pie")
            }
            className="px-2 py-1 border rounded text-xs"
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
            <option value="pie">Pie Chart</option>
          </select>
          <span className="text-gray-500">|</span>
          <button
            onClick={onDuplicate}
            className="px-2 py-1 bg-purple-100 rounded hover:bg-purple-200"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 bg-red-100 rounded hover:bg-red-200"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>

        <input
          type="text"
          value={chartData.title}
          onChange={(e) => handleTitleEdit(e.target.value)}
          className="text-xl font-semibold mb-4 w-full bg-transparent border-b border-gray-300 outline-none text-center"
          placeholder="Chart title..."
        />

        <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-6 rounded-lg">
          <div className="flex items-end space-x-3 h-48">
            {chartData.data.map((item, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full rounded-t transition-all duration-500 hover:opacity-80"
                  style={{
                    backgroundColor: colors[index % colors.length],
                    height: `${(item.value / maxValue) * 160}px`,
                    minHeight: "20px",
                  }}
                />
                <div className="mt-2 text-center text-xs">
                  <div className="font-medium text-gray-700">{item.label}</div>
                  <div className="text-gray-500">
                    {item.value.toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all rounded p-2 ${
        isSelected ? "ring-2 ring-purple-500 bg-purple-50" : "hover:bg-gray-50"
      }`}
      style={style}
    >
      <div className="bg-white border rounded-lg p-6 shadow-sm">
        <h3 className="text-xl font-semibold text-center mb-6 text-gray-800">
          {chartData.title}
        </h3>
        <div className="flex items-end space-x-3 h-48">
          {chartData.data.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t transition-all duration-500 hover:scale-105"
                style={{
                  backgroundColor: colors[index % colors.length],
                  height: `${(item.value / maxValue) * 160}px`,
                  minHeight: "20px",
                }}
              />
              <div className="mt-2 text-center text-xs">
                <div className="font-medium text-gray-700">{item.label}</div>
                <div className="text-gray-500">
                  {item.value.toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Enhanced Interactive Table Component
const InteractiveTable: React.FC<
  BaseComponentProps & {
    content: { headers: string[]; rows: string[][] };
  }
> = ({
  _id,
  content,
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [tableData, setTableData] = useState(content);

  const addRow = useCallback(() => {
    const newRow = Array(tableData.headers.length).fill("New Cell");
    setTableData((prev) => ({
      ...prev,
      rows: [...prev.rows, newRow],
    }));
  }, [tableData.headers.length]);

  const addColumn = useCallback(() => {
    setTableData((prev) => ({
      headers: [...prev.headers, "New Header"],
      rows: prev.rows.map((row) => [...row, "New Cell"]),
    }));
  }, []);

  if (isEditing) {
    return (
      <div
        className={`relative group p-4 border-2 rounded-lg transition-all ${
          isSelected
            ? "border-orange-500 bg-orange-50"
            : "border-gray-300 hover:border-orange-400"
        }`}
        style={style}
      >
        {/* Editing Controls */}
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-orange-600 font-medium">Table</span>
          <span className="text-gray-500">|</span>
          <button
            onClick={addRow}
            className="px-2 py-1 bg-orange-100 rounded hover:bg-orange-200"
          >
            + Row
          </button>
          <button
            onClick={addColumn}
            className="px-2 py-1 bg-orange-100 rounded hover:bg-orange-200"
          >
            + Column
          </button>
          <span className="text-gray-500">|</span>
          <button
            onClick={onDuplicate}
            className="px-2 py-1 bg-orange-100 rounded hover:bg-orange-200"
          >
            <Copy className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 bg-red-100 rounded hover:bg-red-200"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto bg-white rounded-lg border">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-gray-100 to-gray-200">
                {tableData.headers.map((header, index) => (
                  <th
                    key={index}
                    className="border border-gray-300 p-3 text-left"
                  >
                    <input
                      type="text"
                      value={header}
                      onChange={(e) => {
                        const newHeaders = [...tableData.headers];
                        newHeaders[index] = e.target.value;
                        setTableData((prev) => ({
                          ...prev,
                          headers: newHeaders,
                        }));
                      }}
                      className="w-full bg-transparent outline-none font-semibold"
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="border border-gray-300 p-3">
                      <input
                        type="text"
                        value={cell}
                        onChange={(e) => {
                          const newRows = [...tableData.rows];
                          newRows[rowIndex][cellIndex] = e.target.value;
                          setTableData((prev) => ({ ...prev, rows: newRows }));
                        }}
                        className="w-full bg-transparent outline-none"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all rounded p-2 ${
        isSelected ? "ring-2 ring-orange-500 bg-orange-50" : "hover:bg-gray-50"
      }`}
      style={style}
    >
      <div className="overflow-x-auto bg-white rounded-lg border shadow-sm">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gradient-to-r from-gray-100 to-gray-200">
              {tableData.headers.map((header, index) => (
                <th
                  key={index}
                  className="border border-gray-300 p-3 text-left font-semibold text-gray-700"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="border border-gray-300 p-3 text-gray-600"
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

// Main Enhanced Report Builder
const EnhancedNoJSONReportBuilder: React.FC = () => {
  const [reportTitle, setReportTitle] = useState("Interactive Report Builder");
  const [components, setComponents] = useState<ComponentData[]>([]);
  const [previewMode, setPreviewMode] = useState(true);
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(
    null
  );
  const [zoom, setZoom] = useState(100);
  const [showGrid, setShowGrid] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const idCounter = useRef(0);
  const dragIndexRef = useRef<number | null>(null);
  const mainRef = useRef<HTMLDivElement | null>(null);

  const selectedComponent = useMemo(
    () => components.find((c) => c.id === selectedComponentId) || null,
    [components, selectedComponentId]
  );

  // Duplicate Component
  const duplicateComponent = useCallback((id: string) => {
    let newId = "";
    setComponents((prev) => {
      const index = prev.findIndex((c) => c.id === id);
      if (index === -1) return prev;
      const component = prev[index];
      const clone: ComponentData = JSON.parse(JSON.stringify(component));
      idCounter.current += 1;
      newId = `${component.type}-${idCounter.current}`;
      clone.id = newId;
      const next = [
        ...prev.slice(0, index + 1),
        clone,
        ...prev.slice(index + 1),
      ];
      return next;
    });
    if (newId) setSelectedComponentId(newId);
  }, []);

  // Delete Component
  const deleteComponent = useCallback((id: string) => {
    setComponents((prev) => prev.filter((comp) => comp.id !== id));
    setSelectedComponentId(null);
  }, []);

  // Move Component
  const moveComponent = useCallback((id: string, direction: "up" | "down") => {
    setComponents((prev) => {
      const index = prev.findIndex((c) => c.id === id);
      if (index === -1) return prev;
      const newIndex = direction === "up" ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      const copy = [...prev];
      [copy[index], copy[newIndex]] = [copy[newIndex], copy[index]];
      return copy;
    });
  }, []);

  // Load from localStorage on mount
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem("enhancedReport_v1");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed?.reportTitle) setReportTitle(parsed.reportTitle);
        if (Array.isArray(parsed?.components)) setComponents(parsed.components);
      }
    } catch {
      // ignore
    }
  }, []);

  // Keyboard shortcuts
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        handleSave();
      }
      if (!selectedComponentId) return;
      // Duplicate
      if (e.ctrlKey && e.key.toLowerCase() === "d") {
        e.preventDefault();
        duplicateComponent(selectedComponentId);
      }
      // Delete
      if (e.key === "Delete" || (e.ctrlKey && e.key.toLowerCase() === "x")) {
        e.preventDefault();
        deleteComponent(selectedComponentId);
      }
      // Move
      if (e.ctrlKey && e.key === "ArrowUp") {
        e.preventDefault();
        moveComponent(selectedComponentId, "up");
      }
      if (e.ctrlKey && e.key === "ArrowDown") {
        e.preventDefault();
        moveComponent(selectedComponentId, "down");
      }
      // Deselect
      if (e.key === "Escape") {
        setSelectedComponentId(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedComponentId, duplicateComponent, deleteComponent, moveComponent]);

  // Component Templates
  const componentTemplates = useMemo(
    () => ({
      heading: {
        type: "heading" as const,
        content: { content: "New Heading", level: 1 },
        style: { fontSize: "2rem", fontWeight: "bold", color: "#1f2937" },
        isVisible: true,
      },
      paragraph: {
        type: "paragraph" as const,
        content: { content: "Enter your paragraph content here..." },
        style: { fontSize: "1rem", lineHeight: "1.6", color: "#374151" },
        isVisible: true,
      },
      chart: {
        type: "chart" as const,
        content: {
          title: "Sample Chart",
          data: [
            { label: "Q1", value: 120 },
            { label: "Q2", value: 150 },
            { label: "Q3", value: 180 },
            { label: "Q4", value: 200 },
          ],
        },
        style: {},
        isVisible: true,
      },
      table: {
        type: "table" as const,
        content: {
          headers: ["Name", "Value", "Status"],
          rows: [
            ["Item 1", "100", "Active"],
            ["Item 2", "200", "Pending"],
            ["Item 3", "300", "Complete"],
          ],
        },
        style: {},
        isVisible: true,
      },
    }),
    []
  );

  // Add Component
  const addComponent = useCallback(
    (type: keyof typeof componentTemplates) => {
      const template = componentTemplates[type];
      const newComponent: ComponentData = {
        id: `${type}-${++idCounter.current}`,
        ...template,
      };
      setComponents((prev) => [...prev, newComponent]);
      setSelectedComponentId(newComponent.id);
    },
    [componentTemplates]
  );

  // Update Component
  const updateComponent = useCallback(
    (id: string, updates: Partial<ComponentData>) => {
      setComponents((prev) =>
        prev.map((comp) => (comp.id === id ? { ...comp, ...updates } : comp))
      );
    },
    []
  );

  // Save to localStorage
  const handleSave = useCallback(() => {
    try {
      const payload = { reportTitle, components };
      localStorage.setItem("enhancedReport_v1", JSON.stringify(payload));
    } catch {
      // ignore
    }
  }, [reportTitle, components]);

  // Export as HTML (basic)
  const handleExportHTML = useCallback(() => {
    if (!mainRef.current) return;
    const html = `<!doctype html><html><head><meta charset=\"utf-8\"/><title>${
      reportTitle || "Report"
    }</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/></head><body>${
      mainRef.current.innerHTML
    }</body></html>`;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(reportTitle || "report").replace(/\s+/g, "_")}.html`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }, [reportTitle]);
  // Render Component
  const renderComponent = useCallback(
    (component: ComponentData) => {
      const baseProps = {
        isEditing: !previewMode,
        isSelected: selectedComponentId === component.id,
        onEdit: (data: any) => updateComponent(component.id, { content: data }),
        onDelete: () => deleteComponent(component.id),
        onSelect: () => setSelectedComponentId(component.id),
        onDuplicate: () => duplicateComponent(component.id),
        style: component.style,
      } as BaseComponentProps;

      switch (component.type) {
        case "heading":
          return (
            <InteractiveHeading
              {...baseProps}
              id={component.id}
              content={component.content.content}
              level={component.content.level}
            />
          );
        case "paragraph":
          return (
            <InteractiveParagraph
              {...baseProps}
              id={component.id}
              content={component.content.content}
            />
          );
        case "chart":
          return (
            <InteractiveChart
              {...baseProps}
              id={component.id}
              content={component.content}
            />
          );
        case "table":
          return (
            <InteractiveTable
              {...baseProps}
              id={component.id}
              content={component.content}
            />
          );
        default:
          return null;
      }
    },
    [
      previewMode,
      selectedComponentId,
      updateComponent,
      deleteComponent,
      duplicateComponent,
    ]
  );

  // Apply pre-defined templates
  const applyTemplate = useCallback((name: "executive" | "kpi" | "finance") => {
    const createId = (type: ComponentData["type"]) => {
      idCounter.current += 1;
      return `${type}-${idCounter.current}`;
    };

    if (name === "executive") {
      setReportTitle("Executive Summary Report");
      setComponents([
        {
          id: createId("heading"),
          type: "heading",
          content: { content: "Executive Summary", level: 1 },
          style: { fontSize: "2rem", fontWeight: "bold", color: "#1f2937" },
          isVisible: true,
        },
        {
          id: createId("paragraph"),
          type: "paragraph",
          content: {
            content: "This report highlights key insights and outcomes.",
          },
          style: { color: "#374151" },
          isVisible: true,
        },
        {
          id: createId("chart"),
          type: "chart",
          content: {
            title: "Quarterly Performance",
            data: [
              { label: "Q1", value: 120 },
              { label: "Q2", value: 150 },
              { label: "Q3", value: 180 },
              { label: "Q4", value: 200 },
            ],
          },
          style: {},
          isVisible: true,
        },
      ]);
      return;
    }

    if (name === "kpi") {
      setReportTitle("KPI Snapshot");
      setComponents([
        {
          id: createId("heading"),
          type: "heading",
          content: { content: "KPI Overview", level: 1 },
          style: { fontSize: "2rem", fontWeight: "bold" },
          isVisible: true,
        },
        {
          id: createId("table"),
          type: "table",
          content: {
            headers: ["Metric", "Value", "Status"],
            rows: [
              ["Users", "12,450", "Up"],
              ["Revenue", "$58,200", "Up"],
              ["Churn", "2.1%", "Down"],
            ],
          },
          style: {},
          isVisible: true,
        },
      ]);
      return;
    }

    // finance
    setReportTitle("Financial Overview");
    setComponents([
      {
        id: createId("heading"),
        type: "heading",
        content: { content: "Financial Overview", level: 1 },
        style: { fontSize: "2rem", fontWeight: "bold" },
        isVisible: true,
      },
      {
        id: createId("paragraph"),
        type: "paragraph",
        content: {
          content: "Summary of financial performance for the period.",
        },
        style: {},
        isVisible: true,
      },
      {
        id: createId("chart"),
        type: "chart",
        content: {
          title: "Revenue by Quarter",
          data: [
            { label: "Q1", value: 320 },
            { label: "Q2", value: 410 },
            { label: "Q3", value: 380 },
            { label: "Q4", value: 520 },
          ],
        },
        style: {},
        isVisible: true,
      },
    ]);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Enhanced Header */}
      <div className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <FileText className="w-8 h-8 text-blue-600" />
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Enhanced Report Builder
                </h1>
              </div>
              <div className="flex space-x-2">
                <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full flex items-center">
                  <Sparkles className="w-3 h-3 mr-1" />
                  Zero JSON
                </span>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full flex items-center">
                  <Layers className="w-3 h-3 mr-1" />
                  Interactive
                </span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full flex items-center">
                  <Layout className="w-3 h-3 mr-1" />
                  Live Preview
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {/* Zoom Controls */}
              <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setZoom(Math.max(50, zoom - 10))}
                  className="p-1 hover:bg-white rounded"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="text-xs px-2">{zoom}%</span>
                <button
                  onClick={() => setZoom(Math.min(200, zoom + 10))}
                  className="p-1 hover:bg-white rounded"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>

              {/* Grid Toggle */}
              <button
                onClick={() => setShowGrid(!showGrid)}
                className={`p-2 rounded-lg transition-colors ${
                  showGrid
                    ? "bg-blue-100 text-blue-600"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                <Grid className="w-4 h-4" />
              </button>

              {/* Preview Toggle */}
              <button
                onClick={() => {
                  setPreviewMode(!previewMode);
                  setSelectedComponentId(null);
                }}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-all ${
                  previewMode
                    ? "bg-blue-600 text-white shadow-lg"
                    : darkMode
                    ? "bg-gray-800 text-gray-200 hover:bg-gray-700"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                {previewMode ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
                <span>{previewMode ? "Edit Mode" : "Preview"}</span>
              </button>

              {/* Action Buttons */}
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 shadow-lg"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button
                onClick={handleExportHTML}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2 shadow-lg"
              >
                <Download className="w-4 h-4" />
                <span>Export HTML</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Enhanced Sidebar */}
          {!previewMode && (
            <div className="col-span-3 space-y-6">
              {/* Component Library */}
              <div
                className={`${
                  darkMode
                    ? "bg-gray-900 border-gray-800"
                    : "bg-white border-gray-200"
                } rounded-xl shadow-lg p-6 border`}
              >
                <h3
                  className={`text-lg font-semibold mb-4 flex items-center ${
                    darkMode ? "text-gray-100" : "text-gray-800"
                  }`}
                >
                  <Plus className="w-5 h-5 mr-2 text-blue-600" />
                  Add Components
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => addComponent("heading")}
                    className={`p-3 text-left border-2 border-dashed rounded-lg transition-all group ${
                      darkMode
                        ? "border-blue-900 hover:border-blue-700 hover:bg-blue-950"
                        : "border-blue-200 hover:border-blue-400 hover:bg-blue-50"
                    }`}
                  >
                    <Type
                      className={`w-6 h-6 mb-2 group-hover:scale-110 transition-transform ${
                        darkMode ? "text-blue-400" : "text-blue-600"
                      }`}
                    />
                    <div
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-200" : "text-gray-700"
                      }`}
                    >
                      Heading
                    </div>
                  </button>
                  <button
                    onClick={() => addComponent("paragraph")}
                    className={`p-3 text-left border-2 border-dashed rounded-lg transition-all group ${
                      darkMode
                        ? "border-green-900 hover:border-green-700 hover:bg-green-950"
                        : "border-green-200 hover:border-green-400 hover:bg-green-50"
                    }`}
                  >
                    <AlignLeft
                      className={`w-6 h-6 mb-2 group-hover:scale-110 transition-transform ${
                        darkMode ? "text-green-400" : "text-green-600"
                      }`}
                    />
                    <div
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-200" : "text-gray-700"
                      }`}
                    >
                      Paragraph
                    </div>
                  </button>
                  <button
                    onClick={() => addComponent("chart")}
                    className={`p-3 text-left border-2 border-dashed rounded-lg transition-all group ${
                      darkMode
                        ? "border-purple-900 hover:border-purple-700 hover:bg-purple-950"
                        : "border-purple-200 hover:border-purple-400 hover:bg-purple-50"
                    }`}
                  >
                    <BarChart3
                      className={`w-6 h-6 mb-2 group-hover:scale-110 transition-transform ${
                        darkMode ? "text-purple-400" : "text-purple-600"
                      }`}
                    />
                    <div
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-200" : "text-gray-700"
                      }`}
                    >
                      Chart
                    </div>
                  </button>
                  <button
                    onClick={() => addComponent("table")}
                    className={`p-3 text-left border-2 border-dashed rounded-lg transition-all group ${
                      darkMode
                        ? "border-orange-900 hover:border-orange-700 hover:bg-orange-950"
                        : "border-orange-200 hover:border-orange-400 hover:bg-orange-50"
                    }`}
                  >
                    <Table
                      className={`w-6 h-6 mb-2 group-hover:scale-110 transition-transform ${
                        darkMode ? "text-orange-400" : "text-orange-600"
                      }`}
                    />
                    <div
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-200" : "text-gray-700"
                      }`}
                    >
                      Table
                    </div>
                  </button>
                </div>
              </div>

              {/* Templates */}
              <div
                className={`${
                  darkMode
                    ? "bg-gray-900 border-gray-800"
                    : "bg-white border-gray-200"
                } rounded-xl shadow-lg p-6 border`}
              >
                <h3
                  className={`text-lg font-semibold mb-4 flex items-center ${
                    darkMode ? "text-gray-100" : "text-gray-800"
                  }`}
                >
                  <Layout className="w-5 h-5 mr-2 text-purple-600" />
                  Templates
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => applyTemplate("executive")}
                    className={`${
                      darkMode
                        ? "bg-gray-800 hover:bg-gray-700"
                        : "bg-gray-100 hover:bg-gray-200"
                    } w-full p-3 rounded-lg text-left transition`}
                  >
                    Executive Summary
                  </button>
                  <button
                    onClick={() => applyTemplate("kpi")}
                    className={`${
                      darkMode
                        ? "bg-gray-800 hover:bg-gray-700"
                        : "bg-gray-100 hover:bg-gray-200"
                    } w-full p-3 rounded-lg text-left transition`}
                  >
                    KPI Snapshot
                  </button>
                  <button
                    onClick={() => applyTemplate("finance")}
                    className={`${
                      darkMode
                        ? "bg-gray-800 hover:bg-gray-700"
                        : "bg-gray-100 hover:bg-gray-200"
                    } w-full p-3 rounded-lg text-left transition`}
                  >
                    Financial Overview
                  </button>
                </div>
              </div>

              {/* Component Layer Panel (draggable) */}
              <div
                className={`${
                  darkMode
                    ? "bg-gray-900 border-gray-800"
                    : "bg-white border-gray-200"
                } rounded-xl shadow-lg p-6 border`}
              >
                <h3
                  className={`text-lg font-semibold mb-4 flex items-center ${
                    darkMode ? "text-gray-100" : "text-gray-800"
                  }`}
                >
                  <Layers className="w-5 h-5 mr-2 text-purple-600" />
                  Layers ({components.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {components.map((component, index) => (
                    <div
                      key={component.id}
                      className={`flex items-center justify-between p-2 rounded-lg border transition-all ${
                        selectedComponentId === component.id
                          ? "border-blue-500 bg-blue-50"
                          : darkMode
                          ? "border-gray-700 hover:border-gray-600"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                      draggable
                      onDragStart={() => (dragIndexRef.current = index)}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => {
                        if (
                          dragIndexRef.current === null ||
                          dragIndexRef.current === index
                        )
                          return;
                        setComponents((prev) => {
                          const arr = [...prev];
                          const [moved] = arr.splice(
                            dragIndexRef.current as number,
                            1
                          );
                          arr.splice(index, 0, moved);
                          return arr;
                        });
                        dragIndexRef.current = null;
                      }}
                    >
                      <div
                        className="flex items-center space-x-2 flex-1 cursor-pointer"
                        onClick={() => setSelectedComponentId(component.id)}
                      >
                        {component.type === "heading" && (
                          <Type className="w-4 h-4 text-blue-600" />
                        )}
                        {component.type === "paragraph" && (
                          <AlignLeft className="w-4 h-4 text-green-600" />
                        )}
                        {component.type === "chart" && (
                          <BarChart3 className="w-4 h-4 text-purple-600" />
                        )}
                        {component.type === "table" && (
                          <Table className="w-4 h-4 text-orange-600" />
                        )}
                        <span className="text-sm text-gray-700 capitalize">
                          {component.type} {index + 1}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => moveComponent(component.id, "up")}
                          disabled={index === 0}
                          className="p-1 hover:bg-gray-200 rounded disabled:opacity-50"
                        >
                          <ChevronUp className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => moveComponent(component.id, "down")}
                          disabled={index === components.length - 1}
                          className="p-1 hover:bg-gray-200 rounded disabled:opacity-50"
                        >
                          <ChevronDown className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Stats */}
              <div
                className={`${
                  darkMode
                    ? "bg-gradient-to-br from-blue-950 to-purple-950 border-blue-900"
                    : "bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200"
                } rounded-xl p-6 border`}
              >
                <h4 className="font-semibold mb-3 text-gray-800">
                  ✨ Report Stats
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Components:</span>
                    <span className="font-medium">{components.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Headings:</span>
                    <span className="font-medium">
                      {components.filter((c) => c.type === "heading").length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Charts:</span>
                    <span className="font-medium">
                      {components.filter((c) => c.type === "chart").length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tables:</span>
                    <span className="font-medium">
                      {components.filter((c) => c.type === "table").length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content Area */}
          <div className={previewMode ? "col-span-12" : "col-span-6"}>
            <div
              ref={mainRef}
              className={`${
                darkMode
                  ? "bg-gray-900 border-gray-800"
                  : "bg-white border-gray-200"
              } rounded-xl shadow-lg p-8 border transition-all ${
                showGrid ? "bg-grid-pattern" : ""
              }`}
              style={{
                transform: `scale(${zoom / 100})`,
                transformOrigin: "top left",
              }}
            >
              {/* Report Title */}
              <div className="mb-8 pb-6 border-b border-gray-200">
                {previewMode ? (
                  <div>
                    <h1
                      className={`${
                        darkMode
                          ? "text-gray-100"
                          : "bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent"
                      } text-4xl font-bold mb-3`}
                    >
                      {reportTitle}
                    </h1>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>
                        Generated on {new Date().toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <span>{components.length} components</span>
                      <span>•</span>
                      <span>Enhanced Report Builder</span>
                    </div>
                  </div>
                ) : (
                  <div>
                    <input
                      type="text"
                      value={reportTitle}
                      onChange={(e) => setReportTitle(e.target.value)}
                      className={`${
                        darkMode
                          ? "text-gray-100"
                          : "bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent"
                      } text-4xl font-bold mb-3 w-full border-none outline-none focus:ring-2 focus:ring-blue-500 rounded p-2 bg-transparent`}
                      placeholder="Enter your report title..."
                    />
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Live editing mode</span>
                      <span>•</span>
                      <span>Click components to edit</span>
                      <span>•</span>
                      <span>{components.length} components</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Dynamic Component Rendering */}
              <div className="space-y-6">
                {components.map((component) => (
                  <div
                    key={component.id}
                    className="transition-all duration-200"
                  >
                    {renderComponent(component)}
                  </div>
                ))}
              </div>

              {/* Empty State */}
              {components.length === 0 && (
                <div className="text-center py-16">
                  <div className="mb-8">
                    <FileText className="w-24 h-24 mx-auto mb-6 text-gray-300" />
                    <h3 className="text-2xl font-bold mb-3 text-gray-700">
                      Build Your Interactive Report
                    </h3>
                    <p className="text-gray-500 mb-6 max-w-md mx-auto">
                      Start creating with our enhanced component library. No
                      JSON, no complexity - just pure creativity.
                    </p>
                  </div>

                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-8 rounded-2xl text-white inline-block">
                    <div className="text-2xl font-bold mb-2">
                      🚀 Enhanced Features
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center">
                        <Sparkles className="w-4 h-4 mr-2" />
                        Interactive Components
                      </div>
                      <div className="flex items-center">
                        <Layout className="w-4 h-4 mr-2" />
                        Live Preview
                      </div>
                      <div className="flex items-center">
                        <Layers className="w-4 h-4 mr-2" />
                        Layer Management
                      </div>
                      <div className="flex items-center">
                        <PaintBucket className="w-4 h-4 mr-2" />
                        Style Controls
                      </div>
                    </div>
                    <div className="mt-6 flex justify-center">
                      <button
                        onClick={() => applyTemplate("executive")}
                        className="bg-white/90 text-gray-900 px-4 py-2 rounded-lg hover:bg-white"
                      >
                        Use Executive Template
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right-side Style Inspector */}
          {!previewMode && (
            <div className="col-span-3 space-y-6">
              <div
                className={`${
                  darkMode
                    ? "bg-gray-900 border-gray-800"
                    : "bg-white border-gray-200"
                } rounded-xl shadow-lg p-6 border`}
              >
                <h3
                  className={`text-lg font-semibold mb-4 flex items-center ${
                    darkMode ? "text-gray-100" : "text-gray-800"
                  }`}
                >
                  <Settings className="w-5 h-5 mr-2 text-blue-600" />
                  Style Inspector
                </h3>
                {!selectedComponent ? (
                  <div className="text-sm text-gray-500">
                    Select a component to edit its styles.
                  </div>
                ) : (
                  <div className="space-y-4 text-sm">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">
                        Font Size
                      </div>
                      <input
                        type="number"
                        min={10}
                        max={72}
                        value={parseInt(
                          selectedComponent.style?.fontSize?.replace(
                            "px",
                            ""
                          ) || "16"
                        )}
                        onChange={(e) => {
                          const val = `${e.target.value || 16}px`;
                          updateComponent(selectedComponent.id, {
                            style: {
                              ...selectedComponent.style,
                              fontSize: val,
                            },
                          });
                        }}
                        className={`${
                          darkMode
                            ? "bg-gray-800 border-gray-700 text-gray-100"
                            : "bg-white border-gray-300"
                        } w-full border rounded px-2 py-1`}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">
                          Text Color
                        </div>
                        <input
                          type="color"
                          value={selectedComponent.style?.color || "#1f2937"}
                          onChange={(e) =>
                            updateComponent(selectedComponent.id, {
                              style: {
                                ...selectedComponent.style,
                                color: e.target.value,
                              },
                            })
                          }
                          className="w-full h-8"
                        />
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">
                          Background
                        </div>
                        <input
                          type="color"
                          value={
                            selectedComponent.style?.backgroundColor ||
                            "#ffffff"
                          }
                          onChange={(e) =>
                            updateComponent(selectedComponent.id, {
                              style: {
                                ...selectedComponent.style,
                                backgroundColor: e.target.value,
                              },
                            })
                          }
                          className="w-full h-8"
                        />
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">
                        Font Weight
                      </div>
                      <select
                        value={selectedComponent.style?.fontWeight || "normal"}
                        onChange={(e) =>
                          updateComponent(selectedComponent.id, {
                            style: {
                              ...selectedComponent.style,
                              fontWeight: e.target.value as any,
                            },
                          })
                        }
                        className={`${
                          darkMode
                            ? "bg-gray-800 border-gray-700 text-gray-100"
                            : "bg-white border-gray-300"
                        } w-full border rounded px-2 py-1`}
                      >
                        <option value="normal">Normal</option>
                        <option value="500">Medium</option>
                        <option value="bold">Bold</option>
                      </select>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Padding</div>
                      <input
                        type="text"
                        value={selectedComponent.style?.padding || "0"}
                        onChange={(e) =>
                          updateComponent(selectedComponent.id, {
                            style: {
                              ...selectedComponent.style,
                              padding: e.target.value,
                            },
                          })
                        }
                        className={`${
                          darkMode
                            ? "bg-gray-800 border-gray-700 text-gray-100"
                            : "bg-white border-gray-300"
                        } w-full border rounded px-2 py-1`}
                        placeholder="e.g., 8px 12px"
                      />
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Margin</div>
                      <input
                        type="text"
                        value={selectedComponent.style?.margin || "0"}
                        onChange={(e) =>
                          updateComponent(selectedComponent.id, {
                            style: {
                              ...selectedComponent.style,
                              margin: e.target.value,
                            },
                          })
                        }
                        className={`${
                          darkMode
                            ? "bg-gray-800 border-gray-700 text-gray-100"
                            : "bg-white border-gray-300"
                        } w-full border rounded px-2 py-1`}
                        placeholder="e.g., 12px 0"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Visible</span>
                      <input
                        type="checkbox"
                        checked={selectedComponent.isVisible !== false}
                        onChange={(e) =>
                          updateComponent(selectedComponent.id, {
                            isVisible: e.target.checked,
                          })
                        }
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedNoJSONReportBuilder;
