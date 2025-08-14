import { useState, useRef } from "react";
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
} from "lucide-react";

// Type definitions
interface ComponentProps {
  children?: string;
  isEditing?: boolean;
  onEdit?: (data: any) => void;
  onDelete?: () => void;
  style?: React.CSSProperties;
}

interface ChartData {
  label: string;
  value: number;
}

interface TableProps extends ComponentProps {
  headers?: string[];
  rows?: string[][];
}

interface ChartProps extends ComponentProps {
  title?: string;
  data?: ChartData[];
}

// Direct Component Definitions - No JSON!
const ReportHeading: React.FC<ComponentProps> = ({
  children = "",
  isEditing = false,
  onEdit,
  onDelete,
  style = {},
}) => {
  const [text, setText] = useState(children);

  if (isEditing) {
    return (
      <div className="relative group">
        <input
          type="text"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            onEdit(e.target.value);
          }}
          className="text-3xl font-bold text-blue-600 w-full border-2 border-blue-300 rounded p-2 focus:outline-none focus:border-blue-500"
          placeholder="Enter heading..."
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <h1 className="text-3xl font-bold text-blue-600 mb-4" style={style}>
      {text}
    </h1>
  );
};

const ReportParagraph = ({
  children,
  isEditing,
  onEdit,
  onDelete,
  style = {},
}) => {
  const [text, setText] = useState(children);

  if (isEditing) {
    return (
      <div className="relative group">
        <textarea
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            onEdit(e.target.value);
          }}
          className="w-full p-3 border-2 border-gray-300 rounded resize-none focus:outline-none focus:border-blue-500"
          rows={3}
          placeholder="Enter paragraph text..."
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <p className="text-gray-700 leading-relaxed mb-4" style={style}>
      {text}
    </p>
  );
};

const ReportChart = ({
  title,
  data,
  isEditing,
  onEdit,
  onDelete,
  style = {},
}) => {
  const [chartTitle, setChartTitle] = useState(title || "Chart Title");
  const [chartData, setChartData] = useState(
    data || [
      { label: "Jan", value: 100 },
      { label: "Feb", value: 120 },
      { label: "Mar", value: 140 },
    ]
  );

  const maxValue = Math.max(...chartData.map((d) => d.value));

  if (isEditing) {
    return (
      <div className="relative group border-2 border-blue-300 rounded p-4">
        <input
          type="text"
          value={chartTitle}
          onChange={(e) => {
            setChartTitle(e.target.value);
            onEdit({ title: e.target.value, data: chartData });
          }}
          className="text-xl font-semibold mb-4 w-full border border-gray-300 rounded p-2"
          placeholder="Chart title..."
        />
        <div className="flex items-end space-x-4 h-48 bg-gray-50 p-4 rounded">
          {chartData.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-blue-500 rounded-t transition-all duration-300"
                style={{
                  height: `${(item.value / maxValue) * 120}px`,
                  minHeight: "10px",
                }}
              />
              <div className="mt-2 text-center text-sm">
                <div className="font-medium">{item.label}</div>
                <div className="text-gray-600">{item.value}</div>
              </div>
            </div>
          ))}
        </div>
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="mb-6" style={style}>
      <h3 className="text-xl font-semibold mb-4 text-center">{chartTitle}</h3>
      <div className="flex items-end space-x-4 h-48 bg-gray-50 p-4 rounded">
        {chartData.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div
              className="w-full bg-blue-500 rounded-t transition-all duration-300"
              style={{
                height: `${(item.value / maxValue) * 120}px`,
                minHeight: "10px",
              }}
            />
            <div className="mt-2 text-center text-sm">
              <div className="font-medium">{item.label}</div>
              <div className="text-gray-600">{item.value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ReportTable = ({
  headers,
  rows,
  isEditing,
  onEdit,
  onDelete,
  style = {},
}) => {
  const [tableHeaders, setTableHeaders] = useState(
    headers || ["Column 1", "Column 2"]
  );
  const [tableRows, setTableRows] = useState(
    rows || [
      ["Data 1", "Data 2"],
      ["Data 3", "Data 4"],
    ]
  );

  if (isEditing) {
    return (
      <div className="relative group border-2 border-blue-300 rounded p-4">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Table Headers:
          </label>
          <input
            type="text"
            value={tableHeaders.join(", ")}
            onChange={(e) => {
              const newHeaders = e.target.value.split(",").map((h) => h.trim());
              setTableHeaders(newHeaders);
              onEdit({ headers: newHeaders, rows: tableRows });
            }}
            className="w-full border border-gray-300 rounded p-2"
            placeholder="Header 1, Header 2, Header 3..."
          />
        </div>
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              {tableHeaders.map((header, index) => (
                <th
                  key={index}
                  className="border border-gray-300 p-2 text-left"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="border border-gray-300 p-2">
                    <input
                      type="text"
                      value={cell}
                      onChange={(e) => {
                        const newRows = [...tableRows];
                        newRows[rowIndex][cellIndex] = e.target.value;
                        setTableRows(newRows);
                        onEdit({ headers: tableHeaders, rows: newRows });
                      }}
                      className="w-full border-none outline-none"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="mb-6" style={style}>
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            {tableHeaders.map((header, index) => (
              <th
                key={index}
                className="border border-gray-300 p-3 text-left font-semibold"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableRows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="border border-gray-300 p-3">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Main Report Builder Component
const TrueModernReportBuilder = () => {
  const [reportTitle, setReportTitle] = useState("My Report");
  const [components, setComponents] = useState([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [editingComponent, setEditingComponent] = useState(null);
  const componentIdCounter = useRef(0);

  // Add component functions - Direct component creation, no JSON!
  const addHeading = () => {
    const newComponent = {
      id: ++componentIdCounter.current,
      type: "heading",
      component: ReportHeading,
      props: {
        children: "New Heading",
        style: {},
      },
    };
    setComponents([...components, newComponent]);
  };

  const addParagraph = () => {
    const newComponent = {
      id: ++componentIdCounter.current,
      type: "paragraph",
      component: ReportParagraph,
      props: {
        children: "Enter your text here...",
        style: {},
      },
    };
    setComponents([...components, newComponent]);
  };

  const addChart = () => {
    const newComponent = {
      id: ++componentIdCounter.current,
      type: "chart",
      component: ReportChart,
      props: {
        title: "New Chart",
        data: [
          { label: "Jan", value: 100 },
          { label: "Feb", value: 120 },
          { label: "Mar", value: 140 },
        ],
        style: {},
      },
    };
    setComponents([...components, newComponent]);
  };

  const addTable = () => {
    const newComponent = {
      id: ++componentIdCounter.current,
      type: "table",
      component: ReportTable,
      props: {
        headers: ["Column 1", "Column 2"],
        rows: [
          ["Data 1", "Data 2"],
          ["Data 3", "Data 4"],
        ],
        style: {},
      },
    };
    setComponents([...components, newComponent]);
  };

  // Edit component
  const editComponent = (id, newProps) => {
    setComponents(
      components.map((comp) =>
        comp.id === id
          ? { ...comp, props: { ...comp.props, ...newProps } }
          : comp
      )
    );
  };

  // Delete component
  const deleteComponent = (id) => {
    setComponents(components.filter((comp) => comp.id !== id));
    setEditingComponent(null);
  };

  // Export functions
  const exportToPDF = () => {
    alert("PDF export would be implemented here");
  };

  const saveReport = () => {
    alert("Save functionality would be implemented here");
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <FileText className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                True Modern Report Builder
              </h1>
              <div className="text-sm text-green-600 bg-green-100 px-3 py-1 rounded-full">
                🚀 No JSON - Direct Components
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setPreviewMode(!previewMode)}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  previewMode
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>{previewMode ? "Edit Mode" : "Preview"}</span>
              </button>
              <button
                onClick={saveReport}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button
                onClick={exportToPDF}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export PDF</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar - Component Library */}
          {!previewMode && (
            <div className="col-span-3">
              <div className="bg-white rounded-lg shadow p-6 sticky top-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Plus className="w-5 h-5 mr-2" />
                  Add Components
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={addHeading}
                    className="w-full p-3 text-left border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors flex items-center space-x-3"
                  >
                    <Type className="w-5 h-5 text-blue-600" />
                    <span>Heading</span>
                  </button>
                  <button
                    onClick={addParagraph}
                    className="w-full p-3 text-left border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors flex items-center space-x-3"
                  >
                    <AlignLeft className="w-5 h-5 text-blue-600" />
                    <span>Paragraph</span>
                  </button>
                  <button
                    onClick={addChart}
                    className="w-full p-3 text-left border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors flex items-center space-x-3"
                  >
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                    <span>Chart</span>
                  </button>
                  <button
                    onClick={addTable}
                    className="w-full p-3 text-left border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors flex items-center space-x-3"
                  >
                    <Table className="w-5 h-5 text-blue-600" />
                    <span>Table</span>
                  </button>
                </div>

                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-semibold mb-3 text-gray-700">Features</h4>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Direct Component Rendering
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      No JSON Processing
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Live Editing
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Instant Preview
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={previewMode ? "col-span-12" : "col-span-9"}>
            <div className="bg-white rounded-lg shadow p-8">
              {/* Report Title */}
              <div className="mb-8">
                {previewMode ? (
                  <div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                      {reportTitle}
                    </h1>
                    <div className="text-sm text-gray-500">
                      Generated on {new Date().toLocaleDateString()} • True
                      Modern Report Builder
                    </div>
                  </div>
                ) : (
                  <div>
                    <input
                      type="text"
                      value={reportTitle}
                      onChange={(e) => setReportTitle(e.target.value)}
                      className="text-4xl font-bold text-gray-900 mb-2 w-full border-none outline-none focus:ring-2 focus:ring-blue-500 rounded p-2"
                      placeholder="Enter report title..."
                    />
                    <div className="text-sm text-gray-500">
                      Live editing mode • Click components to edit
                    </div>
                  </div>
                )}
              </div>

              {/* Dynamic Components - Rendered Directly! */}
              <div className="space-y-6">
                {components.map((comp) => {
                  const Component = comp.component;
                  return (
                    <div
                      key={comp.id}
                      onClick={() =>
                        !previewMode && setEditingComponent(comp.id)
                      }
                      className={`${
                        !previewMode
                          ? "hover:bg-gray-50 rounded p-2 cursor-pointer"
                          : ""
                      } ${
                        editingComponent === comp.id
                          ? "ring-2 ring-blue-500 bg-blue-50"
                          : ""
                      }`}
                    >
                      <Component
                        {...comp.props}
                        isEditing={!previewMode && editingComponent === comp.id}
                        onEdit={(newData) =>
                          editComponent(
                            comp.id,
                            comp.type === "heading"
                              ? { children: newData }
                              : comp.type === "paragraph"
                              ? { children: newData }
                              : newData
                          )
                        }
                        onDelete={() => deleteComponent(comp.id)}
                      />
                    </div>
                  );
                })}
              </div>

              {/* Empty State */}
              {components.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">
                    Start Building Your Report
                  </h3>
                  <p className="mb-4">
                    Add components from the sidebar to create your report
                  </p>
                  <div className="text-sm text-green-600 bg-green-100 px-4 py-2 rounded-lg inline-block">
                    ✨ No JSON needed - Direct component rendering!
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrueModernReportBuilder;
