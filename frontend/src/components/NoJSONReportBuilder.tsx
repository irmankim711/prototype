import React, { useState, useRef, useMemo } from "react";
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
  Copy,
  Palette,
  Layers,
  ChevronUp,
  ChevronDown,
  EyeOff,
  Settings,
} from "lucide-react";

// Donald Norman-inspired UX improvements applied:
// - Signifiers: visible toolbars, labeled buttons, hover affordances
// - Feedback: selection highlights, hidden badges, disabled states
// - Constraints: hide in preview, disable impossible actions at edges
// - Consistency: theme presets, consistent spacing, component card patterns

// Shared types
interface ComponentStyle {
  fontSize?: string; // e.g. '14px', '1.25rem'
  fontWeight?: string; // 'normal' | 'bold' | numeric
  color?: string;
  backgroundColor?: string;
  padding?: string;
  margin?: string;
  textAlign?: "left" | "center" | "right";
  borderRadius?: string;
  border?: string;
}

interface EditableComponentProps {
  isEditing?: boolean;
  onEdit?: (data: any) => void;
  onDelete?: () => void;
  style?: ComponentStyle;
}

// Theme presets (precompiled Tailwind class tokens)
const THEMES = {
  blue: {
    brandText: "text-blue-600",
    brandBg: "bg-blue-600",
    brandRing: "ring-blue-500",
    brandBadgeText: "text-blue-600",
    brandBadgeBg: "bg-blue-100",
    hoverBg: "hover:bg-blue-50",
    border: "border-blue-300",
  },
  emerald: {
    brandText: "text-emerald-600",
    brandBg: "bg-emerald-600",
    brandRing: "ring-emerald-500",
    brandBadgeText: "text-emerald-600",
    brandBadgeBg: "bg-emerald-100",
    hoverBg: "hover:bg-emerald-50",
    border: "border-emerald-300",
  },
  purple: {
    brandText: "text-purple-600",
    brandBg: "bg-purple-600",
    brandRing: "ring-purple-500",
    brandBadgeText: "text-purple-600",
    brandBadgeBg: "bg-purple-100",
    hoverBg: "hover:bg-purple-50",
    border: "border-purple-300",
  },
  amber: {
    brandText: "text-amber-600",
    brandBg: "bg-amber-600",
    brandRing: "ring-amber-500",
    brandBadgeText: "text-amber-600",
    brandBadgeBg: "bg-amber-100",
    hoverBg: "hover:bg-amber-50",
    border: "border-amber-300",
  },
} as const;

type ThemeKey = keyof typeof THEMES;

// Simple components with inline editing support
const SimpleHeading: React.FC<EditableComponentProps & { text: string }> = ({
  text,
  isEditing = false,
  onEdit,
  onDelete,
  style,
}) => {
  const [content, setContent] = useState(text);

  if (isEditing) {
    return (
      <div className="relative group">
        <input
          type="text"
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            onEdit?.(e.target.value);
          }}
          style={style}
          className="text-3xl font-bold w-full border-2 border-blue-300 rounded p-2 focus:outline-none focus:border-blue-500"
          placeholder="Enter heading..."
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete heading"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <h1
      style={style}
      className="text-3xl font-bold text-gray-900 mb-4"
    >
      {content}
    </h1>
  );
};

const SimpleParagraph: React.FC<EditableComponentProps & { text: string }> = ({
  text,
  isEditing = false,
  onEdit,
  onDelete,
  style,
}) => {
  const [content, setContent] = useState(text);

  if (isEditing) {
    return (
      <div className="relative group">
        <textarea
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            onEdit?.(e.target.value);
          }}
          style={style}
          className="w-full p-3 border-2 border-gray-300 rounded resize-none focus:outline-none focus:border-blue-500"
          rows={3}
          placeholder="Enter text..."
        />
        <button
          onClick={onDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete paragraph"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <p style={style} className="text-gray-700 leading-relaxed mb-4">
      {content}
    </p>
  );
};

const SimpleChart: React.FC<EditableComponentProps & { title: string }> = ({
  title,
  isEditing = false,
  onDelete,
  style,
}) => {
  const [chartTitle, setChartTitle] = useState(title);
  const data = [
    { label: "Jan", value: 100 },
    { label: "Feb", value: 120 },
    { label: "Mar", value: 140 },
    { label: "Apr", value: 110 },
  ];
  const maxValue = Math.max(...data.map((d) => d.value));

  if (isEditing) {
    return (
      <div className="relative group border-2 border-blue-300 rounded p-4" style={style}>
        <input
          type="text"
          value={chartTitle}
          onChange={(e) => setChartTitle(e.target.value)}
          className="text-xl font-semibold mb-4 w-full border border-gray-300 rounded p-2"
          placeholder="Chart title..."
        />
        <div className="flex items-end space-x-4 h-48 bg-gray-50 p-4 rounded">
          {data.map((item, index) => (
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
          title="Delete chart"
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
        {data.map((item, index) => (
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

const SimpleTable: React.FC<EditableComponentProps> = ({ isEditing = false, onDelete, style }) => {
  const headers = ["Product", "Sales", "Growth"];
  const rows = [
    ["Product A", "$10,000", "+15%"],
    ["Product B", "$15,000", "+25%"],
    ["Product C", "$8,000", "+5%"],
  ];

  if (isEditing) {
    return (
      <div className="relative group border-2 border-blue-300 rounded p-4" style={style}>
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              {headers.map((header, index) => (
                <th key={index} className="border border-gray-300 p-2 text-left">
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
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete table"
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
            {headers.map((header, index) => (
              <th key={index} className="border border-gray-300 p-3 text-left font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
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

// Component Registry - Direct component references!
interface ComponentDefinition {
  id: number;
  type: "heading" | "paragraph" | "chart" | "table";
  component: React.ComponentType<any>;
  props: any;
  hidden?: boolean; // constraint: can hide from preview
}

// Main Report Builder - Zero JSON Usage!
const NoJSONReportBuilder: React.FC = () => {
  const [reportTitle, setReportTitle] = useState("Modern Report - No JSON!");
  const [components, setComponents] = useState<ComponentDefinition[]>([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [editingComponent, setEditingComponent] = useState<number | null>(null);
  const [theme, setTheme] = useState<ThemeKey>("blue");
  const componentIdCounter = useRef(0);

  const t = THEMES[theme];

  // Add component functions - Direct instantiation!
  const addHeading = () => {
    const newComponent: ComponentDefinition = {
      id: ++componentIdCounter.current,
      type: "heading",
      component: SimpleHeading,
      props: { text: "New Heading", style: { margin: "0 0 0.5rem 0" } },
    };
    setComponents((prev) => [...prev, newComponent]);
  };

  const addParagraph = () => {
    const newComponent: ComponentDefinition = {
      id: ++componentIdCounter.current,
      type: "paragraph",
      component: SimpleParagraph,
      props: { text: "Enter your text here..." },
    };
    setComponents((prev) => [...prev, newComponent]);
  };

  const addChart = () => {
    const newComponent: ComponentDefinition = {
      id: ++componentIdCounter.current,
      type: "chart",
      component: SimpleChart,
      props: { title: "Sample Chart" },
    };
    setComponents((prev) => [...prev, newComponent]);
  };

  const addTable = () => {
    const newComponent: ComponentDefinition = {
      id: ++componentIdCounter.current,
      type: "table",
      component: SimpleTable,
      props: {},
    };
    setComponents((prev) => [...prev, newComponent]);
  };

  // Generic prop update
  const updateComponentProps = (id: number, newProps: any) => {
    setComponents((prev) =>
      prev.map((c) => (c.id === id ? { ...c, props: { ...c.props, ...newProps } } : c))
    );
  };

  // Edit text content quickly
  const editComponent = (id: number, newData: any) => {
    setComponents((prev) =>
      prev.map((comp) => (comp.id === id ? { ...comp, props: { ...comp.props, text: newData } } : comp))
    );
  };

  // Delete component - Direct removal!
  const deleteComponent = (id: number) => {
    setComponents((prev) => prev.filter((comp) => comp.id !== id));
    setEditingComponent(null);
  };

  // Reorder and duplicate with constraints
  const moveComponent = (id: number, direction: "up" | "down") => {
    setComponents((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      if (idx === -1) return prev;
      const newIndex = direction === "up" ? idx - 1 : idx + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev; // constraint: no-op at edges
      const newArr = [...prev];
      const [item] = newArr.splice(idx, 1);
      newArr.splice(newIndex, 0, item);
      return newArr;
    });
  };

  const duplicateComponent = (id: number) => {
    setComponents((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      if (idx === -1) return prev;
      const original = prev[idx];
      const clone: ComponentDefinition = {
        ...original,
        id: ++componentIdCounter.current,
      };
      const arr = [...prev];
      arr.splice(idx + 1, 0, clone);
      return arr;
    });
  };

  const toggleHidden = (id: number) => {
    setComponents((prev) => prev.map((c) => (c.id === id ? { ...c, hidden: !c.hidden } : c)));
  };

  const activeComp = useMemo(
    () => components.find((c) => c.id === editingComponent) || null,
    [components, editingComponent]
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <FileText className={`w-8 h-8 ${t.brandText}`} />
              <h1 className="text-2xl font-bold text-gray-900">No-JSON Report Builder</h1>
              <div className="hidden sm:flex space-x-2">
                <div className={`text-xs ${t.brandBadgeText} ${t.brandBadgeBg} px-2 py-1 rounded-full`}>
                  ✅ Zero JSON
                </div>
                <div className={`text-xs ${t.brandBadgeText} ${t.brandBadgeBg} px-2 py-1 rounded-full`}>
                  🚀 Direct Components
                </div>
                <div className={`text-xs ${t.brandBadgeText} ${t.brandBadgeBg} px-2 py-1 rounded-full`}>
                  ⚡ Live Editing
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="hidden md:flex items-center space-x-2 mr-2">
                <Palette className={`w-4 h-4 ${t.brandText}`} />
                {(Object.keys(THEMES) as ThemeKey[]).map((k) => (
                  <button
                    key={k}
                    onClick={() => setTheme(k)}
                    title={`Theme: ${k}`}
                    className={`w-5 h-5 rounded-full border ${THEMES[k].border} ${THEMES[k].brandBg} ${
                      theme === k ? "ring-2 ring-offset-2 " + THEMES[k].brandRing : ""
                    }`}
                  />
                ))}
              </div>
              <button
                onClick={() => setPreviewMode(!previewMode)}
                title={previewMode ? "Switch to Edit Mode" : "Preview the report"}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  previewMode ? `${t.brandBg} text-white` : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>{previewMode ? "Edit Mode" : "Preview"}</span>
              </button>
              <button
                className={`px-4 py-2 ${t.brandBg} text-white rounded-lg hover:opacity-90 transition-colors flex items-center space-x-2`}
                title="Save report"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2"
                title="Export report"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar: Add components */}
          {!previewMode && (
            <div className="col-span-12 md:col-span-3 order-1 md:order-none">
              <div className="bg-white rounded-lg shadow p-6 sticky top-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Plus className={`w-5 h-5 mr-2 ${t.brandText}`} />
                  Add Components
                </h3>
                <div className="space-y-3">
                  <button
                    onClick={addHeading}
                    className={`w-full p-3 text-left border rounded-lg ${t.hoverBg} ${t.border} transition-all flex items-center space-x-3`}
                    title="Add a heading"
                  >
                    <Type className={`w-5 h-5 ${t.brandText}`} />
                    <span>Heading</span>
                  </button>
                  <button
                    onClick={addParagraph}
                    className={`w-full p-3 text-left border rounded-lg ${t.hoverBg} ${t.border} transition-all flex items-center space-x-3`}
                    title="Add a paragraph"
                  >
                    <AlignLeft className={`w-5 h-5 ${t.brandText}`} />
                    <span>Paragraph</span>
                  </button>
                  <button
                    onClick={addChart}
                    className={`w-full p-3 text-left border rounded-lg ${t.hoverBg} ${t.border} transition-all flex items-center space-x-3`}
                    title="Add a chart"
                  >
                    <BarChart3 className={`w-5 h-5 ${t.brandText}`} />
                    <span>Chart</span>
                  </button>
                  <button
                    onClick={addTable}
                    className={`w-full p-3 text-left border rounded-lg ${t.hoverBg} ${t.border} transition-all flex items-center space-x-3`}
                    title="Add a table"
                  >
                    <Table className={`w-5 h-5 ${t.brandText}`} />
                    <span>Table</span>
                  </button>
                </div>

                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-semibold mb-3 text-gray-700">✨ Features</h4>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Direct React Components
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Zero JSON Processing
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Live Preview
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      Instant Updates
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={previewMode ? "col-span-12" : "col-span-12 md:col-span-6"}>
            <div className="bg-white rounded-lg shadow p-8">
              {/* Report Title */}
              <div className="mb-8">
                {previewMode ? (
                  <div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">{reportTitle}</h1>
                    <div className="text-sm text-gray-500">
                      Generated {new Date().toLocaleDateString()} • No-JSON Report Builder
                    </div>
                  </div>
                ) : (
                  <div>
                    <input
                      type="text"
                      value={reportTitle}
                      onChange={(e) => setReportTitle(e.target.value)}
                      className={`text-4xl font-bold text-gray-900 mb-2 w-full border-none outline-none focus:ring-2 rounded p-2 ${t.brandRing.replace("ring-", "focus:ring-")}`}
                      placeholder="Enter report title..."
                      aria-label="Report title"
                    />
                    <div className="text-sm text-gray-500">Live editing mode • Click any component to edit</div>
                  </div>
                )}
              </div>

              {/* Direct Component Rendering - NO JSON! */}
              <div className="space-y-6">
                {components.map((comp, index) => {
                  const Component = comp.component as React.ComponentType<any>;
                  const isActive = editingComponent === comp.id && !previewMode;

                  if (previewMode && comp.hidden) {
                    return null; // constraint: hidden in preview
                  }

                  return (
                    <div
                      key={comp.id}
                      onClick={() => !previewMode && setEditingComponent(comp.id)}
                      className={`relative transition-all ${
                        !previewMode
                          ? `hover:bg-gray-50 rounded-lg p-3 cursor-pointer ${
                              isActive ? `ring-2 ${t.brandRing} bg-blue-50` : ""
                            }`
                          : ""
                      }`}
                    >
                      {/* Visibility status in edit mode */}
                      {!previewMode && comp.hidden && (
                        <span className="absolute -top-2 left-2 text-xs bg-gray-800 text-white px-2 py-0.5 rounded">
                          Hidden in Preview
                        </span>
                      )}

                      {/* Toolbar (signifiers) */}
                      {!previewMode && (
                        <div className="absolute -top-3 right-2 flex items-center space-x-1 bg-white shadow-sm border rounded px-2 py-1 opacity-0 hover:opacity-100 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              moveComponent(comp.id, "up");
                            }}
                            className="p-1 rounded hover:bg-gray-100"
                            title="Move up"
                            disabled={index === 0}
                          >
                            <ChevronUp className={`w-4 h-4 ${index === 0 ? "text-gray-300" : "text-gray-700"}`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              moveComponent(comp.id, "down");
                            }}
                            className="p-1 rounded hover:bg-gray-100"
                            title="Move down"
                            disabled={index === components.length - 1}
                          >
                            <ChevronDown
                              className={`w-4 h-4 ${index === components.length - 1 ? "text-gray-300" : "text-gray-700"}`}
                            />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              duplicateComponent(comp.id);
                            }}
                            className="p-1 rounded hover:bg-gray-100"
                            title="Duplicate"
                          >
                            <Copy className="w-4 h-4 text-gray-700" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleHidden(comp.id);
                            }}
                            className="p-1 rounded hover:bg-gray-100"
                            title={comp.hidden ? "Show in preview" : "Hide in preview"}
                          >
                            <EyeOff className={`w-4 h-4 ${comp.hidden ? "text-amber-600" : "text-gray-700"}`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteComponent(comp.id);
                            }}
                            className="p-1 rounded hover:bg-gray-100"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
                          </button>
                        </div>
                      )}

                      <Component
                        {...comp.props}
                        isEditing={!previewMode && isActive}
                        onEdit={(newData: any) => editComponent(comp.id, newData)}
                        onDelete={() => deleteComponent(comp.id)}
                      />
                    </div>
                  );
                })}
              </div>

              {/* Empty State */}
              {components.length === 0 && (
                <div className="text-center py-16">
                  <FileText className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                  <h3 className="text-xl font-medium mb-3 text-gray-700">Start Building Your Report</h3>
                  <p className="text-gray-500 mb-6">Add components from the sidebar to create your report</p>
                  <div className="bg-gradient-to-r from-green-100 to-blue-100 p-6 rounded-xl inline-block">
                    <div className="text-lg font-semibold text-gray-800 mb-2">🎉 No More JSON!</div>
                    <div className="text-sm text-gray-600">
                      Direct component rendering • Faster • Cleaner • More intuitive
                    </div>
                  </div>
                  {!previewMode && (
                    <div className="mt-6">
                      <button
                        onClick={addHeading}
                        className={`px-4 py-2 rounded-lg ${t.brandBg} text-white hover:opacity-90 inline-flex items-center space-x-2`}
                        title="Quick add heading"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Add first heading</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Inspector: contextual settings for selected component */}
          {!previewMode && (
            <div className="col-span-12 md:col-span-3">
              <div className="bg-white rounded-lg shadow p-6 sticky top-6">
                <h3 className="text-lg font-semibold mb-1 flex items-center">
                  <Settings className={`w-5 h-5 mr-2 ${t.brandText}`} /> Inspector
                </h3>
                <p className="text-xs text-gray-500 mb-4">Select a component to customize its appearance</p>

                {!activeComp && (
                  <div className="text-sm text-gray-500">
                    No component selected. Click a component on the canvas to edit.
                  </div>
                )}

                {activeComp && (
                  <div className="space-y-4">
                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Type</div>
                      <div className="text-sm capitalize flex items-center space-x-2">
                        <Layers className={`w-4 h-4 ${t.brandText}`} />
                        <span>{activeComp.type}</span>
                      </div>
                    </div>

                    {/* Alignment */}
                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Text align</div>
                      <div className="flex items-center space-x-2">
                        {["left", "center", "right"].map((align) => (
                          <button
                            key={align}
                            onClick={() =>
                              updateComponentProps(activeComp.id, {
                                style: { ...(activeComp.props?.style || {}), textAlign: align as "left" | "center" | "right" },
                              })
                            }
                            className={`px-3 py-1 text-sm border rounded ${
                              activeComp.props?.style?.textAlign === align ? `${t.brandBg} text-white` : "bg-white"
                            }`}
                          >
                            {align}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Font size */}
                    <div>
                      <label className="text-xs font-medium text-gray-500 mb-1 block">Font size</label>
                      <select
                        value={activeComp.props?.style?.fontSize || ""}
                        onChange={(e) =>
                          updateComponentProps(activeComp.id, {
                            style: { ...(activeComp.props?.style || {}), fontSize: e.target.value || undefined },
                          })
                        }
                        className="w-full border rounded p-2 text-sm"
                      >
                        <option value="">Default</option>
                        <option value="0.875rem">Small</option>
                        <option value="1rem">Normal</option>
                        <option value="1.25rem">Large</option>
                        <option value="1.5rem">XL</option>
                      </select>
                    </div>

                    {/* Weight */}
                    <div>
                      <label className="text-xs font-medium text-gray-500 mb-1 block">Font weight</label>
                      <select
                        value={activeComp.props?.style?.fontWeight || ""}
                        onChange={(e) =>
                          updateComponentProps(activeComp.id, {
                            style: { ...(activeComp.props?.style || {}), fontWeight: e.target.value || undefined },
                          })
                        }
                        className="w-full border rounded p-2 text-sm"
                      >
                        <option value="">Default</option>
                        <option value="400">Regular</option>
                        <option value="600">Semi-bold</option>
                        <option value="700">Bold</option>
                      </select>
                    </div>

                    {/* Color */}
                    <div>
                      <label className="text-xs font-medium text-gray-500 mb-1 block">Text color</label>
                      <input
                        type="color"
                        value={activeComp.props?.style?.color || "#1f2937"}
                        onChange={(e) =>
                          updateComponentProps(activeComp.id, {
                            style: { ...(activeComp.props?.style || {}), color: e.target.value },
                          })
                        }
                        className="w-full h-8 p-0 border rounded"
                      />
                    </div>

                    {/* Spacing */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-gray-500 mb-1 block">Padding</label>
                        <input
                          type="text"
                          placeholder="e.g. 8px 12px"
                          value={activeComp.props?.style?.padding || ""}
                          onChange={(e) =>
                            updateComponentProps(activeComp.id, {
                              style: { ...(activeComp.props?.style || {}), padding: e.target.value || undefined },
                            })
                          }
                          className="w-full border rounded p-2 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 mb-1 block">Border radius</label>
                        <input
                          type="text"
                          placeholder="e.g. 8px"
                          value={activeComp.props?.style?.borderRadius || ""}
                          onChange={(e) =>
                            updateComponentProps(activeComp.id, {
                              style: { ...(activeComp.props?.style || {}), borderRadius: e.target.value || undefined },
                            })
                          }
                          className="w-full border rounded p-2 text-sm"
                        />
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="pt-2 border-t mt-2 flex items-center justify-between">
                      <div className="text-xs text-gray-500">Component ID: {activeComp.id}</div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => duplicateComponent(activeComp.id)}
                          className="px-2 py-1 text-sm border rounded hover:bg-gray-50"
                          title="Duplicate"
                        >
                          <Copy className="w-4 h-4 inline mr-1" /> Duplicate
                        </button>
                        <button
                          onClick={() => toggleHidden(activeComp.id)}
                          className="px-2 py-1 text-sm border rounded hover:bg-gray-50"
                          title={activeComp.hidden ? "Show in preview" : "Hide in preview"}
                        >
                          <EyeOff className="w-4 h-4 inline mr-1" /> {activeComp.hidden ? "Show" : "Hide"}
                        </button>
                        <button
                          onClick={() => deleteComponent(activeComp.id)}
                          className="px-2 py-1 text-sm border rounded hover:bg-red-50 text-red-600"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4 inline mr-1" /> Delete
                        </button>
                      </div>
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

export default NoJSONReportBuilder;
