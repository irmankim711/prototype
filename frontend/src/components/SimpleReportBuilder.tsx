import React, { useState } from "react";
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
} from "lucide-react";

// Simple Direct Components - No JSON, No Complex Data Structures!
const EditableHeading: React.FC<{
  text: string;
  onChange: (text: string) => void;
  onDelete: () => void;
  isEditing: boolean;
}> = ({ text, onChange, onDelete, isEditing }) => {
  if (isEditing) {
    return (
      <div className="relative group border-2 border-blue-300 p-2 rounded">
        <input
          type="text"
          value={text}
          onChange={(e) => onChange(e.target.value)}
          className="text-2xl font-bold text-blue-600 w-full bg-transparent outline-none"
          placeholder="Enter heading..."
        />
        <button
          onClick={onDelete}
          className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="relative group">
      <h2 className="text-2xl font-bold text-blue-600 cursor-pointer hover:bg-blue-50 p-2 rounded">
        {text}
      </h2>
    </div>
  );
};

const EditableParagraph: React.FC<{
  text: string;
  onChange: (text: string) => void;
  onDelete: () => void;
  isEditing: boolean;
}> = ({ text, onChange, onDelete, isEditing }) => {
  if (isEditing) {
    return (
      <div className="relative group border-2 border-green-300 p-2 rounded">
        <textarea
          value={text}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-transparent outline-none resize-none"
          rows={4}
          placeholder="Enter paragraph text..."
        />
        <button
          onClick={onDelete}
          className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="relative group">
      <p className="text-gray-700 leading-relaxed cursor-pointer hover:bg-gray-50 p-2 rounded">
        {text}
      </p>
    </div>
  );
};

const SimpleChart: React.FC<{
  title: string;
  onTitleChange: (title: string) => void;
  onDelete: () => void;
  isEditing: boolean;
}> = ({ title, onTitleChange, onDelete, isEditing }) => {
  // Simple hardcoded data - no complex structures
  const chartData = [
    { name: "Jan", value: 100 },
    { name: "Feb", value: 120 },
    { name: "Mar", value: 140 },
    { name: "Apr", value: 160 },
  ];

  const maxValue = Math.max(...chartData.map((d) => d.value));

  if (isEditing) {
    return (
      <div className="relative group border-2 border-purple-300 p-4 rounded">
        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          className="text-lg font-semibold w-full bg-transparent outline-none text-center mb-4"
          placeholder="Chart title..."
        />
        <div className="flex items-end space-x-2 h-32">
          {chartData.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-purple-500 rounded-t"
                style={{
                  height: `${(item.value / maxValue) * 100}px`,
                  minHeight: "10px",
                }}
              />
              <div className="text-xs mt-1">{item.name}</div>
            </div>
          ))}
        </div>
        <button
          onClick={onDelete}
          className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="relative group border p-4 rounded cursor-pointer hover:bg-gray-50">
      <h3 className="text-lg font-semibold text-center mb-4">{title}</h3>
      <div className="flex items-end space-x-2 h-32">
        {chartData.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div
              className="w-full bg-blue-500 rounded-t"
              style={{
                height: `${(item.value / maxValue) * 100}px`,
                minHeight: "10px",
              }}
            />
            <div className="text-xs mt-1">{item.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SimpleTable: React.FC<{
  onDelete: () => void;
  isEditing: boolean;
}> = ({ onDelete, isEditing }) => {
  // Simple hardcoded table - no complex data
  const headers = ["Name", "Value", "Status"];
  const rows = [
    ["Item 1", "100", "Active"],
    ["Item 2", "200", "Pending"],
    ["Item 3", "300", "Complete"],
  ];

  if (isEditing) {
    return (
      <div className="relative group border-2 border-orange-300 p-4 rounded">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {headers.map((header, index) => (
                <th
                  key={index}
                  className="border border-gray-300 p-2 bg-gray-100 text-left"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="border border-gray-300 p-2">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <button
          onClick={onDelete}
          className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div className="relative group cursor-pointer hover:bg-gray-50 p-2 rounded">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th
                key={index}
                className="border border-gray-300 p-2 bg-gray-100 text-left"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="border border-gray-300 p-2">
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

// Main Component - Absolutely NO JSON!
const SimpleReportBuilder: React.FC = () => {
  const [reportTitle, setReportTitle] = useState("My Simple Report");
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [editingComponent, setEditingComponent] = useState<number | null>(null);

  // Simple arrays - no complex objects!
  const [headings, setHeadings] = useState<string[]>(["Welcome to Our Report"]);
  const [paragraphs, setParagraphs] = useState<string[]>([
    "This is a sample paragraph. Click to edit when not in preview mode.",
  ]);
  const [chartTitles, setChartTitles] = useState<string[]>(["Sample Chart"]);
  const [tableCount, setTableCount] = useState(1);

  // Component management - simple arrays only!
  const [componentOrder, setComponentOrder] = useState<string[]>([
    "heading-0",
    "paragraph-0",
    "chart-0",
    "table-0",
  ]);

  const addComponent = (type: string) => {
    const newId = Date.now();
    switch (type) {
      case "heading":
        setHeadings([...headings, "New Heading"]);
        setComponentOrder([...componentOrder, `heading-${headings.length}`]);
        break;
      case "paragraph":
        setParagraphs([...paragraphs, "New paragraph text..."]);
        setComponentOrder([
          ...componentOrder,
          `paragraph-${paragraphs.length}`,
        ]);
        break;
      case "chart":
        setChartTitles([...chartTitles, "New Chart"]);
        setComponentOrder([...componentOrder, `chart-${chartTitles.length}`]);
        break;
      case "table":
        setTableCount(tableCount + 1);
        setComponentOrder([...componentOrder, `table-${tableCount}`]);
        break;
    }
  };

  const deleteComponent = (componentId: string) => {
    setComponentOrder(componentOrder.filter((id) => id !== componentId));
  };

  const updateHeading = (index: number, newText: string) => {
    const newHeadings = [...headings];
    newHeadings[index] = newText;
    setHeadings(newHeadings);
  };

  const updateParagraph = (index: number, newText: string) => {
    const newParagraphs = [...paragraphs];
    newParagraphs[index] = newText;
    setParagraphs(newParagraphs);
  };

  const updateChartTitle = (index: number, newTitle: string) => {
    const newTitles = [...chartTitles];
    newTitles[index] = newTitle;
    setChartTitles(newTitles);
  };

  const renderComponent = (componentId: string, index: number) => {
    const [type, indexStr] = componentId.split("-");
    const componentIndex = parseInt(indexStr);
    const isEditing = editingComponent === index && !isPreviewMode;

    switch (type) {
      case "heading":
        return (
          <div key={componentId} onClick={() => setEditingComponent(index)}>
            <EditableHeading
              text={headings[componentIndex] || ""}
              onChange={(text) => updateHeading(componentIndex, text)}
              onDelete={() => deleteComponent(componentId)}
              isEditing={isEditing}
            />
          </div>
        );
      case "paragraph":
        return (
          <div key={componentId} onClick={() => setEditingComponent(index)}>
            <EditableParagraph
              text={paragraphs[componentIndex] || ""}
              onChange={(text) => updateParagraph(componentIndex, text)}
              onDelete={() => deleteComponent(componentId)}
              isEditing={isEditing}
            />
          </div>
        );
      case "chart":
        return (
          <div key={componentId} onClick={() => setEditingComponent(index)}>
            <SimpleChart
              title={chartTitles[componentIndex] || ""}
              onTitleChange={(title) => updateChartTitle(componentIndex, title)}
              onDelete={() => deleteComponent(componentId)}
              isEditing={isEditing}
            />
          </div>
        );
      case "table":
        return (
          <div key={componentId} onClick={() => setEditingComponent(index)}>
            <SimpleTable
              onDelete={() => deleteComponent(componentId)}
              isEditing={isEditing}
            />
          </div>
        );
      default:
        return null;
    }
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
                Simple Report Builder
              </h1>
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm font-medium">
                NO JSON!
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  setIsPreviewMode(!isPreviewMode);
                  setEditingComponent(null);
                }}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  isPreviewMode
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>{isPreviewMode ? "Edit Mode" : "Preview"}</span>
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar - Simple Component Adder */}
          {!isPreviewMode && (
            <div className="col-span-3">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Add Components</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => addComponent("heading")}
                    className="w-full p-3 text-left border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors flex items-center space-x-3"
                  >
                    <Type className="w-5 h-5 text-blue-600" />
                    <span>Add Heading</span>
                  </button>
                  <button
                    onClick={() => addComponent("paragraph")}
                    className="w-full p-3 text-left border rounded-lg hover:bg-green-50 hover:border-green-300 transition-colors flex items-center space-x-3"
                  >
                    <AlignLeft className="w-5 h-5 text-green-600" />
                    <span>Add Paragraph</span>
                  </button>
                  <button
                    onClick={() => addComponent("chart")}
                    className="w-full p-3 text-left border rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors flex items-center space-x-3"
                  >
                    <BarChart3 className="w-5 h-5 text-purple-600" />
                    <span>Add Chart</span>
                  </button>
                  <button
                    onClick={() => addComponent("table")}
                    className="w-full p-3 text-left border rounded-lg hover:bg-orange-50 hover:border-orange-300 transition-colors flex items-center space-x-3"
                  >
                    <Table className="w-5 h-5 text-orange-600" />
                    <span>Add Table</span>
                  </button>
                </div>

                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-semibold mb-3">Instructions</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Click components to edit them</li>
                    <li>• Use Preview mode to see final result</li>
                    <li>• No JSON data anywhere!</li>
                    <li>• Simple direct components only</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={isPreviewMode ? "col-span-12" : "col-span-9"}>
            <div className="bg-white rounded-lg shadow p-8">
              {/* Report Title */}
              <div className="mb-8">
                {isPreviewMode ? (
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {reportTitle}
                  </h1>
                ) : (
                  <input
                    type="text"
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    className="text-3xl font-bold text-gray-900 mb-2 w-full border-2 border-blue-300 rounded p-2 outline-none focus:border-blue-500"
                    placeholder="Enter report title..."
                  />
                )}
                <div className="text-sm text-gray-500">
                  Generated on {new Date().toLocaleDateString()}
                </div>
              </div>

              {/* Dynamic Content - Simple Arrays Only! */}
              <div className="space-y-6">
                {componentOrder.map((componentId, index) =>
                  renderComponent(componentId, index)
                )}
              </div>

              {componentOrder.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">
                    Start Building Your Simple Report
                  </h3>
                  <p>Add components from the sidebar - No JSON required!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleReportBuilder;
