import React, {
  useState,
  useRef,
  useCallback,
  useMemo,
  useEffect,
} from "react";
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
  Moon,
  Sun,
  Undo,
  Redo,
  Share,
  Heart,
  Star,
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  Minimize2,
} from "lucide-react";

// Enhanced Theme System
interface Theme {
  name: string;
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  gradient: string;
}

const themes: Record<string, Theme> = {
  light: {
    name: "Light",
    primary: "#3B82F6",
    secondary: "#8B5CF6",
    accent: "#10B981",
    background: "linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)",
    surface: "rgba(255, 255, 255, 0.8)",
    text: "#1F2937",
    textSecondary: "#6B7280",
    border: "rgba(209, 213, 219, 0.5)",
    success: "#10B981",
    warning: "#F59E0B",
    error: "#EF4444",
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  },
  dark: {
    name: "Dark",
    primary: "#60A5FA",
    secondary: "#A78BFA",
    accent: "#34D399",
    background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
    surface: "rgba(30, 41, 59, 0.8)",
    text: "#F8FAFC",
    textSecondary: "#94A3B8",
    border: "rgba(71, 85, 105, 0.5)",
    success: "#34D399",
    warning: "#FBBF24",
    error: "#F87171",
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  },
  ocean: {
    name: "Ocean",
    primary: "#0EA5E9",
    secondary: "#06B6D4",
    accent: "#14B8A6",
    background: "linear-gradient(135deg, #0C4A6E 0%, #164E63 100%)",
    surface: "rgba(7, 89, 133, 0.8)",
    text: "#F0F9FF",
    textSecondary: "#7DD3FC",
    border: "rgba(14, 165, 233, 0.3)",
    success: "#14B8A6",
    warning: "#F59E0B",
    error: "#F87171",
    gradient: "linear-gradient(135deg, #0ea5e9 0%, #14b8a6 100%)",
  },
};

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
  borderRadius?: string;
  textAlign?: "left" | "center" | "right";
  width?: string;
  animation?: string;
}

interface ReportComponent {
  id: string;
  type: "heading" | "paragraph" | "chart" | "table" | "image" | "list";
  content: any;
  style: ComponentStyle;
  metadata: {
    created: Date;
    modified: Date;
    version: number;
  };
}

// Modern Animated Heading Component
const ModernHeading: React.FC<
  BaseComponentProps & { content: string; level: 1 | 2 | 3 | 4 | 5 | 6 }
> = ({
  id,
  content,
  level = 1,
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [text, setText] = useState(content);
  const [isAnimating, setIsAnimating] = useState(false);

  const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements;

  const handleEdit = useCallback(
    (newText: string) => {
      setText(newText);
      onEdit?.({ content: newText });
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), 300);
    },
    [onEdit]
  );

  const defaultStyles = {
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
        <div className="absolute -inset-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative backdrop-blur-sm bg-white/10 rounded-lg p-4 border border-white/20">
          <input
            type="text"
            value={text}
            onChange={(e) => handleEdit(e.target.value)}
            className={`${
              defaultStyles[`h${level}` as keyof typeof defaultStyles]
            } w-full bg-transparent outline-none text-white placeholder-gray-300`}
            placeholder={`Enter ${HeadingTag.toUpperCase()} heading...`}
            style={style}
          />
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={onDuplicate}
              className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 rounded-full text-blue-200 text-xs transition-all"
            >
              <Copy className="w-3 h-3" />
            </button>
            <button
              onClick={onDelete}
              className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-full text-red-200 text-xs transition-all"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-300 rounded-lg p-3 ${
        isSelected
          ? "ring-2 ring-blue-400 bg-blue-50/50 backdrop-blur-sm shadow-lg transform scale-[1.02]"
          : "hover:bg-white/10 hover:backdrop-blur-sm hover:shadow-md"
      } ${isAnimating ? "animate-pulse" : ""}`}
    >
      <HeadingTag
        className={`${
          defaultStyles[`h${level}` as keyof typeof defaultStyles]
        } text-gray-800 dark:text-white transition-colors duration-300`}
        style={style}
      >
        {text}
      </HeadingTag>
    </div>
  );
};

// Modern Interactive Paragraph Component
const ModernParagraph: React.FC<BaseComponentProps & { content: string }> = ({
  id,
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
  const [wordCount, setWordCount] = useState(0);

  const handleEdit = useCallback(
    (newText: string) => {
      setText(newText);
      onEdit?.({ content: newText });
      setWordCount(newText.split(/\s+/).filter(Boolean).length);
    },
    [onEdit]
  );

  useEffect(() => {
    setWordCount(text.split(/\s+/).filter(Boolean).length);
  }, [text]);

  if (isEditing) {
    return (
      <div className="relative group">
        <div className="absolute -inset-2 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative backdrop-blur-sm bg-white/10 rounded-lg p-4 border border-white/20">
          <textarea
            value={text}
            onChange={(e) => handleEdit(e.target.value)}
            className="w-full h-32 bg-transparent outline-none text-white placeholder-gray-300 resize-none"
            placeholder="Enter your paragraph content..."
            style={style}
          />
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              <button
                onClick={onDuplicate}
                className="px-3 py-1 bg-green-500/20 hover:bg-green-500/30 rounded-full text-green-200 text-xs transition-all"
              >
                <Copy className="w-3 h-3" />
              </button>
              <button
                onClick={onDelete}
                className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-full text-red-200 text-xs transition-all"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
            <span className="text-xs text-gray-300">{wordCount} words</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-300 rounded-lg p-3 ${
        isSelected
          ? "ring-2 ring-green-400 bg-green-50/50 backdrop-blur-sm shadow-lg transform scale-[1.01]"
          : "hover:bg-white/10 hover:backdrop-blur-sm hover:shadow-md"
      }`}
    >
      <p
        className="text-gray-700 dark:text-gray-200 leading-relaxed transition-colors duration-300"
        style={style}
      >
        {text}
      </p>
      {isSelected && (
        <div className="mt-2 text-xs text-gray-500">{wordCount} words</div>
      )}
    </div>
  );
};

// Ultra-Modern Interactive Chart Component
const ModernChart: React.FC<
  BaseComponentProps & {
    title: string;
    chartType: "bar" | "line" | "pie" | "area";
    data: Array<{ label: string; value: number; color?: string }>;
  }
> = ({
  id,
  title,
  chartType = "bar",
  data = [],
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [chartData, setChartData] = useState({ title, data, type: chartType });
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsAnimating(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const colors = [
    "#3B82F6",
    "#8B5CF6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#06B6D4",
    "#84CC16",
    "#F97316",
    "#EC4899",
    "#6366F1",
  ];

  const maxValue = Math.max(...chartData.data.map((d) => d.value), 1);

  const handleDataEdit = (
    index: number,
    field: "label" | "value",
    newValue: string
  ) => {
    const newData = [...chartData.data];
    if (field === "value") {
      newData[index] = { ...newData[index], value: parseFloat(newValue) || 0 };
    } else {
      newData[index] = { ...newData[index], label: newValue };
    }
    setChartData({ ...chartData, data: newData });
    onEdit?.({ title: chartData.title, data: newData, type: chartData.type });
  };

  if (isEditing) {
    return (
      <div className="relative group">
        <div className="absolute -inset-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/20">
          {/* Chart Controls */}
          <div className="flex items-center gap-4 mb-4">
            <select
              value={chartData.type}
              onChange={(e) => {
                const newType = e.target.value as typeof chartType;
                setChartData({ ...chartData, type: newType });
                onEdit?.({ ...chartData, type: newType });
              }}
              className="px-3 py-1 bg-white/20 border border-white/30 rounded-lg text-white text-sm backdrop-blur-sm"
            >
              <option value="bar" className="text-gray-800">
                Bar Chart
              </option>
              <option value="line" className="text-gray-800">
                Line Chart
              </option>
              <option value="pie" className="text-gray-800">
                Pie Chart
              </option>
              <option value="area" className="text-gray-800">
                Area Chart
              </option>
            </select>
            <div className="flex gap-2">
              <button
                onClick={onDuplicate}
                className="px-3 py-1 bg-purple-500/20 hover:bg-purple-500/30 rounded-full text-purple-200 text-xs transition-all"
              >
                <Copy className="w-3 h-3" />
              </button>
              <button
                onClick={onDelete}
                className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-full text-red-200 text-xs transition-all"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>

          <input
            type="text"
            value={chartData.title}
            onChange={(e) => {
              setChartData({ ...chartData, title: e.target.value });
              onEdit?.({ ...chartData, title: e.target.value });
            }}
            className="text-xl font-semibold mb-6 w-full bg-transparent border-b border-white/30 outline-none text-center text-white placeholder-gray-300"
            placeholder="Chart title..."
          />

          {/* Data Editor */}
          <div className="space-y-2 mb-4">
            {chartData.data.map((item, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={item.label}
                  onChange={(e) =>
                    handleDataEdit(index, "label", e.target.value)
                  }
                  className="flex-1 px-2 py-1 bg-white/20 border border-white/30 rounded text-white text-sm"
                  placeholder="Label"
                />
                <input
                  type="number"
                  value={item.value}
                  onChange={(e) =>
                    handleDataEdit(index, "value", e.target.value)
                  }
                  className="w-20 px-2 py-1 bg-white/20 border border-white/30 rounded text-white text-sm"
                  placeholder="Value"
                />
              </div>
            ))}
          </div>

          {/* Chart Visualization */}
          <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <div className="flex items-end space-x-3 h-48">
              {chartData.data.map((item, index) => (
                <div
                  key={index}
                  className="flex-1 flex flex-col items-center group"
                >
                  <div className="relative w-full">
                    <div
                      className="w-full rounded-t-lg transition-all duration-1000 hover:opacity-80 cursor-pointer"
                      style={{
                        backgroundColor: colors[index % colors.length],
                        height: `${(item.value / maxValue) * 180}px`,
                        minHeight: "10px",
                        background: `linear-gradient(135deg, ${
                          colors[index % colors.length]
                        } 0%, ${colors[(index + 1) % colors.length]} 100%)`,
                        boxShadow: `0 4px 20px ${
                          colors[index % colors.length]
                        }40`,
                        transform: isAnimating ? `scaleY(0)` : `scaleY(1)`,
                        transformOrigin: "bottom",
                        animation: isAnimating
                          ? `slideUp 0.8s ease-out ${index * 0.1}s forwards`
                          : "",
                      }}
                    />
                  </div>
                  <div className="text-xs mt-2 text-center text-white/90">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-white/70">{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-300 rounded-xl p-4 ${
        isSelected
          ? "ring-2 ring-purple-400 bg-purple-50/50 backdrop-blur-sm shadow-xl transform scale-[1.02]"
          : "hover:bg-white/10 hover:backdrop-blur-sm hover:shadow-lg"
      }`}
    >
      <h3 className="text-xl font-semibold text-center mb-6 text-gray-800 dark:text-white">
        {chartData.title}
      </h3>
      <div className="bg-gradient-to-br from-gray-50/80 to-gray-100/80 dark:from-gray-800/80 dark:to-gray-900/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
        <div className="flex items-end space-x-3 h-48">
          {chartData.data.map((item, index) => (
            <div
              key={index}
              className="flex-1 flex flex-col items-center group"
            >
              <div className="relative w-full">
                <div
                  className="w-full rounded-t-lg transition-all duration-700 hover:opacity-80 cursor-pointer hover:scale-105"
                  style={{
                    height: `${(item.value / maxValue) * 180}px`,
                    minHeight: "10px",
                    background: `linear-gradient(135deg, ${
                      colors[index % colors.length]
                    } 0%, ${colors[(index + 1) % colors.length]} 100%)`,
                    boxShadow: `0 4px 20px ${colors[index % colors.length]}40`,
                  }}
                />
                <div className="absolute inset-0 bg-white/20 rounded-t-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </div>
              <div className="text-xs mt-2 text-center">
                <div className="font-medium text-gray-700 dark:text-gray-300">
                  {item.label}
                </div>
                <div className="text-gray-500 dark:text-gray-400">
                  {item.value}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Modern Table Component
const ModernTable: React.FC<
  BaseComponentProps & {
    headers: string[];
    rows: string[][];
  }
> = ({
  id,
  headers = [],
  rows = [],
  isEditing,
  isSelected,
  onEdit,
  onDelete,
  onSelect,
  onDuplicate,
  style = {},
}) => {
  const [tableData, setTableData] = useState({ headers, rows });

  const handleCellEdit = (
    rowIndex: number,
    colIndex: number,
    value: string
  ) => {
    const newRows = [...tableData.rows];
    newRows[rowIndex][colIndex] = value;
    setTableData({ ...tableData, rows: newRows });
    onEdit?.({ headers: tableData.headers, rows: newRows });
  };

  const handleHeaderEdit = (index: number, value: string) => {
    const newHeaders = [...tableData.headers];
    newHeaders[index] = value;
    setTableData({ ...tableData, headers: newHeaders });
    onEdit?.({ headers: newHeaders, rows: tableData.rows });
  };

  if (isEditing) {
    return (
      <div className="relative group">
        <div className="absolute -inset-2 bg-gradient-to-r from-orange-500 to-red-600 rounded-lg blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/20">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={onDuplicate}
              className="px-3 py-1 bg-orange-500/20 hover:bg-orange-500/30 rounded-full text-orange-200 text-xs transition-all"
            >
              <Copy className="w-3 h-3" />
            </button>
            <button
              onClick={onDelete}
              className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-full text-red-200 text-xs transition-all"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-hidden rounded-lg border border-white/30 backdrop-blur-sm">
            <table className="w-full">
              <thead>
                <tr className="bg-gradient-to-r from-orange-500/20 to-red-500/20">
                  {tableData.headers.map((header, index) => (
                    <th key={index} className="p-3 text-left">
                      <input
                        type="text"
                        value={header}
                        onChange={(e) =>
                          handleHeaderEdit(index, e.target.value)
                        }
                        className="w-full bg-transparent text-white font-semibold outline-none"
                        placeholder={`Header ${index + 1}`}
                      />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableData.rows.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="border-t border-white/20 hover:bg-white/5"
                  >
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="p-3">
                        <input
                          type="text"
                          value={cell}
                          onChange={(e) =>
                            handleCellEdit(rowIndex, cellIndex, e.target.value)
                          }
                          className="w-full bg-transparent text-white outline-none"
                          placeholder="Cell data"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-300 rounded-xl p-4 ${
        isSelected
          ? "ring-2 ring-orange-400 bg-orange-50/50 backdrop-blur-sm shadow-xl transform scale-[1.01]"
          : "hover:bg-white/10 hover:backdrop-blur-sm hover:shadow-lg"
      }`}
    >
      <div className="overflow-hidden rounded-lg border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm">
        <table className="w-full bg-white/80 dark:bg-gray-800/80">
          <thead>
            <tr className="bg-gradient-to-r from-orange-500/10 to-red-500/10">
              {tableData.headers.map((header, index) => (
                <th
                  key={index}
                  className="p-3 text-left font-semibold text-gray-800 dark:text-white"
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
                className="border-t border-gray-200/50 dark:border-gray-700/50 hover:bg-gray-50/50 dark:hover:bg-gray-700/50 transition-colors"
              >
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="p-3 text-gray-700 dark:text-gray-300"
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

// Main Enhanced Report Builder Component
const UltraModernReportBuilder: React.FC = () => {
  const [currentTheme, setCurrentTheme] =
    useState<keyof typeof themes>("light");
  const [reportTitle, setReportTitle] = useState("Ultra-Modern Report");
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(
    null
  );
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Component state management
  const [components, setComponents] = useState<ReportComponent[]>([
    {
      id: "1",
      type: "heading",
      content: { text: "Welcome to the Future of Reports", level: 1 },
      style: { textAlign: "center", color: themes[currentTheme].primary },
      metadata: { created: new Date(), modified: new Date(), version: 1 },
    },
    {
      id: "2",
      type: "paragraph",
      content: {
        text: "This is an ultra-modern, interactive report builder with stunning visual design, smooth animations, and advanced functionality. Experience the future of document creation.",
      },
      style: { textAlign: "left" },
      metadata: { created: new Date(), modified: new Date(), version: 1 },
    },
    {
      id: "3",
      type: "chart",
      content: {
        title: "Performance Metrics",
        type: "bar",
        data: [
          { label: "Q1", value: 85 },
          { label: "Q2", value: 92 },
          { label: "Q3", value: 78 },
          { label: "Q4", value: 96 },
        ],
      },
      style: {},
      metadata: { created: new Date(), modified: new Date(), version: 1 },
    },
    {
      id: "4",
      type: "table",
      content: {
        headers: ["Metric", "Current", "Target", "Status"],
        rows: [
          ["Revenue", "$1.2M", "$1.5M", "🟡 In Progress"],
          ["Users", "50K", "75K", "🟢 On Track"],
          ["Retention", "85%", "90%", "🟡 In Progress"],
        ],
      },
      style: {},
      metadata: { created: new Date(), modified: new Date(), version: 1 },
    },
  ]);

  const theme = themes[currentTheme];

  // Component management functions
  const addComponent = useCallback((type: ReportComponent["type"]) => {
    const newComponent: ReportComponent = {
      id: Date.now().toString(),
      type,
      content: getDefaultContent(type),
      style: {},
      metadata: { created: new Date(), modified: new Date(), version: 1 },
    };
    setComponents((prev) => [...prev, newComponent]);
  }, []);

  const deleteComponent = useCallback(
    (id: string) => {
      setComponents((prev) => prev.filter((comp) => comp.id !== id));
      if (selectedComponent === id) setSelectedComponent(null);
      if (editingComponent === id) setEditingComponent(null);
    },
    [selectedComponent, editingComponent]
  );

  const duplicateComponent = useCallback(
    (id: string) => {
      const component = components.find((comp) => comp.id === id);
      if (component) {
        const newComponent: ReportComponent = {
          ...component,
          id: Date.now().toString(),
          metadata: { created: new Date(), modified: new Date(), version: 1 },
        };
        setComponents((prev) => [...prev, newComponent]);
      }
    },
    [components]
  );

  const updateComponent = useCallback(
    (id: string, updates: Partial<ReportComponent>) => {
      setComponents((prev) =>
        prev.map((comp) =>
          comp.id === id
            ? {
                ...comp,
                ...updates,
                metadata: {
                  ...comp.metadata,
                  modified: new Date(),
                  version: comp.metadata.version + 1,
                },
              }
            : comp
        )
      );
    },
    []
  );

  function getDefaultContent(type: ReportComponent["type"]) {
    switch (type) {
      case "heading":
        return { text: "New Heading", level: 2 };
      case "paragraph":
        return { text: "Enter your content here..." };
      case "chart":
        return {
          title: "New Chart",
          type: "bar",
          data: [
            { label: "A", value: 10 },
            { label: "B", value: 20 },
            { label: "C", value: 15 },
          ],
        };
      case "table":
        return {
          headers: ["Column 1", "Column 2"],
          rows: [
            ["Data 1", "Data 2"],
            ["Data 3", "Data 4"],
          ],
        };
      default:
        return {};
    }
  }

  const renderComponent = (component: ReportComponent) => {
    const commonProps = {
      id: component.id,
      isEditing: editingComponent === component.id,
      isSelected: selectedComponent === component.id,
      onEdit: (data: any) =>
        updateComponent(component.id, {
          content: { ...component.content, ...data },
        }),
      onDelete: () => deleteComponent(component.id),
      onSelect: () => setSelectedComponent(component.id),
      onDuplicate: () => duplicateComponent(component.id),
      style: component.style,
    };

    switch (component.type) {
      case "heading":
        return (
          <ModernHeading
            key={component.id}
            {...commonProps}
            content={component.content.text}
            level={component.content.level}
          />
        );
      case "paragraph":
        return (
          <ModernParagraph
            key={component.id}
            {...commonProps}
            content={component.content.text}
          />
        );
      case "chart":
        return (
          <ModernChart
            key={component.id}
            {...commonProps}
            title={component.content.title}
            chartType={component.content.type}
            data={component.content.data}
          />
        );
      case "table":
        return (
          <ModernTable
            key={component.id}
            {...commonProps}
            headers={component.content.headers}
            rows={component.content.rows}
          />
        );
      default:
        return null;
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "s":
            e.preventDefault();
            // Save logic here
            break;
          case "z":
            e.preventDefault();
            // Undo logic here
            break;
          case "y":
            e.preventDefault();
            // Redo logic here
            break;
        }
      }
      if (e.key === "Escape") {
        setEditingComponent(null);
        setSelectedComponent(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div
      className="min-h-screen transition-all duration-500"
      style={{ background: theme.background }}
    >
      {/* Ultra-Modern Header */}
      <div
        className="backdrop-blur-md border-b sticky top-0 z-50 transition-all duration-300"
        style={{
          backgroundColor: theme.surface,
          borderColor: theme.border,
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Ultra Report Builder
                  </h1>
                  <p className="text-xs text-gray-500">
                    Next-generation document creation
                  </p>
                </div>
              </div>

              {/* Theme Selector */}
              <div className="flex items-center space-x-2">
                {Object.keys(themes).map((themeName) => (
                  <button
                    key={themeName}
                    onClick={() =>
                      setCurrentTheme(themeName as keyof typeof themes)
                    }
                    className={`p-2 rounded-lg transition-all ${
                      currentTheme === themeName
                        ? "ring-2 ring-offset-2 ring-blue-500"
                        : "hover:bg-gray-100 dark:hover:bg-gray-700"
                    }`}
                    title={`Switch to ${
                      themes[themeName as keyof typeof themes].name
                    } theme`}
                  >
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{
                        background:
                          themes[themeName as keyof typeof themes].gradient,
                      }}
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Advanced Controls */}
            <div className="flex items-center space-x-3">
              {/* Zoom Controls */}
              <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-white/10 backdrop-blur-sm">
                <button
                  onClick={() => setZoomLevel(Math.max(50, zoomLevel - 10))}
                  className="p-1 hover:bg-white/20 rounded"
                >
                  <ZoomOut className="w-4 h-4" style={{ color: theme.text }} />
                </button>
                <span
                  className="text-sm font-medium"
                  style={{ color: theme.text }}
                >
                  {zoomLevel}%
                </span>
                <button
                  onClick={() => setZoomLevel(Math.min(200, zoomLevel + 10))}
                  className="p-1 hover:bg-white/20 rounded"
                >
                  <ZoomIn className="w-4 h-4" style={{ color: theme.text }} />
                </button>
              </div>

              {/* Action Buttons */}
              <button
                onClick={() => setIsPreviewMode(!isPreviewMode)}
                className="px-4 py-2 rounded-xl flex items-center space-x-2 transition-all transform hover:scale-105 shadow-lg"
                style={{
                  background: isPreviewMode
                    ? theme.gradient
                    : `${theme.surface}`,
                  color: isPreviewMode ? "white" : theme.text,
                  border: `1px solid ${theme.border}`,
                }}
              >
                <Eye className="w-4 h-4" />
                <span>{isPreviewMode ? "Edit Mode" : "Preview"}</span>
              </button>

              <button
                className="px-4 py-2 rounded-xl flex items-center space-x-2 transition-all transform hover:scale-105 shadow-lg"
                style={{
                  background: theme.success,
                  color: "white",
                }}
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>

              <button
                className="px-4 py-2 rounded-xl flex items-center space-x-2 transition-all transform hover:scale-105 shadow-lg"
                style={{
                  background: theme.secondary,
                  color: "white",
                }}
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>

              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 rounded-xl transition-all transform hover:scale-105 shadow-lg"
                style={{
                  background: theme.surface,
                  color: theme.text,
                  border: `1px solid ${theme.border}`,
                }}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div
          className={`grid gap-6 transition-all duration-300 ${
            isFullscreen ? "grid-cols-1" : "grid-cols-12"
          }`}
        >
          {/* Advanced Sidebar */}
          {!isPreviewMode && !isFullscreen && (
            <div className="col-span-3">
              <div
                className="backdrop-blur-md rounded-2xl p-6 border sticky top-24 shadow-xl"
                style={{
                  backgroundColor: theme.surface,
                  borderColor: theme.border,
                }}
              >
                <h3
                  className="text-lg font-semibold mb-6 flex items-center"
                  style={{ color: theme.text }}
                >
                  <Layers className="w-5 h-5 mr-2" />
                  Components
                </h3>

                {/* Component Buttons */}
                <div className="space-y-3 mb-6">
                  {[
                    {
                      type: "heading",
                      icon: Type,
                      label: "Heading",
                      color: theme.primary,
                    },
                    {
                      type: "paragraph",
                      icon: AlignLeft,
                      label: "Paragraph",
                      color: theme.success,
                    },
                    {
                      type: "chart",
                      icon: BarChart3,
                      label: "Chart",
                      color: theme.secondary,
                    },
                    {
                      type: "table",
                      icon: Table,
                      label: "Table",
                      color: theme.warning,
                    },
                  ].map(({ type, icon: Icon, label, color }) => (
                    <button
                      key={type}
                      onClick={() =>
                        addComponent(type as ReportComponent["type"])
                      }
                      className="w-full p-4 text-left rounded-xl transition-all transform hover:scale-105 hover:shadow-lg group"
                      style={{
                        background: `linear-gradient(135deg, ${color}15 0%, ${color}25 100%)`,
                        border: `1px solid ${color}30`,
                      }}
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className="p-2 rounded-lg"
                          style={{ backgroundColor: `${color}20` }}
                        >
                          <Icon className="w-5 h-5" style={{ color }} />
                        </div>
                        <div>
                          <div
                            className="font-medium"
                            style={{ color: theme.text }}
                          >
                            {label}
                          </div>
                          <div
                            className="text-xs"
                            style={{ color: theme.textSecondary }}
                          >
                            Add {label.toLowerCase()}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Component List */}
                <div
                  className="border-t pt-6"
                  style={{ borderColor: theme.border }}
                >
                  <h4
                    className="font-medium mb-3"
                    style={{ color: theme.text }}
                  >
                    Document Structure
                  </h4>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {components.map((component, index) => (
                      <div
                        key={component.id}
                        onClick={() => setSelectedComponent(component.id)}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          selectedComponent === component.id
                            ? "ring-2 ring-blue-400 transform scale-105"
                            : "hover:bg-white/10"
                        }`}
                        style={{
                          backgroundColor:
                            selectedComponent === component.id
                              ? `${theme.primary}20`
                              : "transparent",
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: theme.primary }}
                            />
                            <span
                              className="text-sm font-medium"
                              style={{ color: theme.text }}
                            >
                              {component.type} {index + 1}
                            </span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingComponent(
                                editingComponent === component.id
                                  ? null
                                  : component.id
                              );
                            }}
                            className="p-1 rounded hover:bg-white/20"
                          >
                            <Settings
                              className="w-3 h-3"
                              style={{ color: theme.textSecondary }}
                            />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Stats */}
                <div
                  className="border-t pt-4 mt-6"
                  style={{ borderColor: theme.border }}
                >
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div
                      className="p-3 rounded-lg"
                      style={{ backgroundColor: `${theme.primary}15` }}
                    >
                      <div
                        className="text-lg font-bold"
                        style={{ color: theme.primary }}
                      >
                        {components.length}
                      </div>
                      <div
                        className="text-xs"
                        style={{ color: theme.textSecondary }}
                      >
                        Components
                      </div>
                    </div>
                    <div
                      className="p-3 rounded-lg"
                      style={{ backgroundColor: `${theme.success}15` }}
                    >
                      <div
                        className="text-lg font-bold"
                        style={{ color: theme.success }}
                      >
                        {zoomLevel}%
                      </div>
                      <div
                        className="text-xs"
                        style={{ color: theme.textSecondary }}
                      >
                        Zoom
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content Area */}
          <div
            className={`${
              isFullscreen
                ? "col-span-1"
                : isPreviewMode
                ? "col-span-12"
                : "col-span-9"
            }`}
          >
            <div
              className="backdrop-blur-md rounded-2xl p-8 border shadow-xl"
              style={{
                backgroundColor: theme.surface,
                borderColor: theme.border,
                transform: `scale(${zoomLevel / 100})`,
                transformOrigin: "top left",
              }}
            >
              {/* Report Title */}
              <div className="mb-8">
                {isPreviewMode ? (
                  <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {reportTitle}
                  </h1>
                ) : (
                  <input
                    type="text"
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    className="text-4xl font-bold mb-2 w-full bg-transparent outline-none bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent placeholder-gray-400"
                    placeholder="Enter report title..."
                  />
                )}
                <div className="text-sm" style={{ color: theme.textSecondary }}>
                  Last modified: {new Date().toLocaleDateString()} •{" "}
                  {components.length} components
                </div>
              </div>

              {/* Dynamic Content */}
              <div className="space-y-8">{components.map(renderComponent)}</div>

              {components.length === 0 && (
                <div className="text-center py-16">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                    <Sparkles className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3
                    className="text-xl font-semibold mb-2"
                    style={{ color: theme.text }}
                  >
                    Start Creating Something Amazing
                  </h3>
                  <p
                    className="text-sm mb-6"
                    style={{ color: theme.textSecondary }}
                  >
                    Add components from the sidebar to build your ultra-modern
                    report
                  </p>
                  <button
                    onClick={() => addComponent("heading")}
                    className="px-6 py-3 rounded-xl font-medium transition-all transform hover:scale-105 shadow-lg"
                    style={{
                      background: theme.gradient,
                      color: "white",
                    }}
                  >
                    Add Your First Component
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Custom CSS for animations */}
      <style jsx>{`
        @keyframes slideUp {
          from {
            transform: scaleY(0);
            opacity: 0;
          }
          to {
            transform: scaleY(1);
            opacity: 1;
          }
        }

        .animate-slideUp {
          animation: slideUp 0.8s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default UltraModernReportBuilder;
