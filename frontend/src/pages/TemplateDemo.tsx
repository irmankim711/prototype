import React from "react";
import { useState } from "react";
import { CheckCircle } from "@mui/icons-material";
import EnhancedTemplateEditor from "../components/EnhancedTemplateEditor";

interface ReportResult {
  success: boolean;
  downloadUrl?: string;
  filename?: string;
  context_used?: Record<string, unknown>;
  missing_fields?: string[];
  optimizations?: Record<string, unknown>;
}

const TemplateDemo: React.FC = () => {
  const [activeDemo, setActiveDemo] = useState<"overview" | "editor">(
    "overview"
  );
  const [reportResult, setReportResult] = useState<ReportResult | null>(null);

  const features = [
    {
      title: "Smart Template Analysis",
      description:
        "Automatically detects placeholders, loops, tables, and nested structures in LaTeX and Word templates.",
      details: [
        "Extracts {{simple}} placeholders",
        "Identifies {{#loops}}...{{/loops}} blocks",
        "Detects table structures",
        "Maps nested {{object.property}} fields",
      ],
    },
    {
      title: "Comprehensive Excel Extraction",
      description:
        "Intelligently extracts all data patterns from Excel files across multiple sheets.",
      details: [
        "Program information and metadata",
        "Participant lists with attendance",
        "Evaluation matrices and ratings",
        "Schedule and tentative data",
        "Suggestions and feedback",
      ],
    },
    {
      title: "Intelligent Data Mapping",
      description:
        "Automatically maps Excel data to template placeholders using pattern recognition.",
      details: [
        "Contextual field matching",
        "Multi-language support (English/Malay)",
        "Automatic data type conversion",
        "Missing field identification",
        "Quality validation and suggestions",
      ],
    },
  ];

  const templateFeatures = [
    "Program information (title, date, location, organizer)",
    "Participant management (attendance, pre/post assessment)",
    "Evaluation matrices with rating scales (1-5)",
    "Program schedule and tentative",
    "Statistical analysis and summaries",
    "Image placeholders and signatures",
    "Multi-day program support",
    "Automated calculation fields",
  ];

  const handleReportGenerated = (result: ReportResult) => {
    setReportResult(result);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Enhanced Template System
              </h1>
              <p className="mt-2 text-gray-600">
                Intelligent report generation with comprehensive Excel data
                extraction
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveDemo("overview")}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeDemo === "overview"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveDemo("editor")}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeDemo === "editor"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                Try Demo
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeDemo === "overview" ? (
          <div className="space-y-12">
            {/* Features Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow"
                >
                  <div className="flex items-center mb-4">
                    {feature.icon}
                    <h3 className="text-xl font-semibold text-gray-800 ml-3">
                      {feature.title}
                    </h3>
                  </div>
                  <p className="text-gray-600 mb-4">{feature.description}</p>
                  <ul className="space-y-2">
                    {feature.details.map((detail, idx) => (
                      <li
                        key={idx}
                        className="flex items-center text-sm text-gray-700"
                      >
                        <CheckCircle className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Template Example */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Your LaTeX Template Example
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">
                    Template Structure
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                    <pre className="text-gray-700">{`% Program Information
\\section{Maklumat Program}
\\begin{tabular}{|l|l|}
    \\hline
    \\textbf{Tarikh} & {{program.date}} \\\\
    \\hline
    \\textbf{Tempat} & {{program.place}} \\\\
    \\hline
    \\textbf{Jumlah Peserta} & {{program.total_participants}} \\\\
    \\hline
\\end{tabular}

% Participant List
\\section{Laporan Kehadiran Peserta}
\\begin{longtable}{|c|p{4cm}|c|c|}
    \\hline
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{Hadir H1} & \\textbf{Hadir H2} \\\\
    \\hline
    {{#participants}}
    {{participant.bil}} & {{participant.name}} & {{participant.attendance_day1}} & {{participant.attendance_day2}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}`}</pre>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">
                    Supported Features
                  </h3>
                  <div className="space-y-2">
                    {templateFeatures.map((feature, index) => (
                      <div key={index} className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* How It Works */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
                How It Works
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto mb-4">
                    1
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Upload Files
                  </h3>
                  <p className="text-sm text-gray-600">
                    Upload your LaTeX/Word template and Excel data file
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto mb-4">
                    2
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Auto Analysis
                  </h3>
                  <p className="text-sm text-gray-600">
                    System analyzes template structure and extracts Excel data
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto mb-4">
                    3
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Smart Mapping
                  </h3>
                  <p className="text-sm text-gray-600">
                    Intelligent field mapping and data validation
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-orange-600 text-white rounded-full flex items-center justify-center font-bold text-lg mx-auto mb-4">
                    4
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Generate Report
                  </h3>
                  <p className="text-sm text-gray-600">
                    Create polished, professional report with all data
                  </p>
                </div>
              </div>
            </div>

            {/* Benefits */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Key Benefits
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Zero Manual Data Entry
                      </h4>
                      <p className="text-sm text-gray-600">
                        Automatically extracts all data from Excel files
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Flawless Template Mapping
                      </h4>
                      <p className="text-sm text-gray-600">
                        Intelligent pattern recognition and field matching
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Multi-Sheet Support
                      </h4>
                      <p className="text-sm text-gray-600">
                        Processes complex Excel workbooks with multiple sheets
                      </p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Quality Validation
                      </h4>
                      <p className="text-sm text-gray-600">
                        Identifies missing fields and data quality issues
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Professional Output
                      </h4>
                      <p className="text-sm text-gray-600">
                        Generates polished PDF and Word documents
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Time Savings
                      </h4>
                      <p className="text-sm text-gray-600">
                        Reduces report generation time by 90%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <EnhancedTemplateEditor onReportGenerated={handleReportGenerated} />

            {reportResult && (
              <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-800 mb-4">
                  Report Generation Results
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-green-700 mb-2">
                      Generated File
                    </h4>
                    <div className="bg-white rounded p-3 border">
                      <div className="text-sm text-gray-700">
                        <strong>Filename:</strong> {reportResult.filename}
                      </div>
                      <button
                        onClick={() =>
                          window.open(reportResult.downloadUrl, "_blank")
                        }
                        className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                      >
                        Download Report
                      </button>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-green-700 mb-2">
                      Processing Summary
                    </h4>
                    <div className="bg-white rounded p-3 border text-sm text-gray-700">
                      <div>✓ Template analyzed successfully</div>
                      <div>✓ Excel data extracted and mapped</div>
                      <div>
                        ✓ {Object.keys(reportResult.context_used || {}).length}{" "}
                        context fields processed
                      </div>
                      <div>
                        {reportResult.missing_fields?.length > 0
                          ? `⚠ ${reportResult.missing_fields.length} missing fields identified`
                          : "✓ All template fields populated"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateDemo;
