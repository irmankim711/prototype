import React from "react";
import { useState, useCallback } from "react";
import {
  Upload,
  File,
  FileText,
  Download,
  AlertCircle,
  CheckCircle,
  Loader,
} from "lucide-react";

interface EnhancedTemplateEditorProps {
  onReportGenerated?: (result: any) => void;
}

interface OptimizationResult {
  success: boolean;
  template_analysis?: any;
  data_extraction?: any;
  context?: any;
  missing_fields?: string[];
  optimizations?: any;
  error?: string;
}

const EnhancedTemplateEditor: React.FC<EnhancedTemplateEditorProps> = ({
  onReportGenerated,
}) => {
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [optimizationResult, setOptimizationResult] =
    useState<OptimizationResult | null>(null);
  const [generatedReport, setGeneratedReport] = useState<any>(null);

  const handleTemplateUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        const allowedTypes = [".tex", ".docx"];
        const fileExtension = file.name
          .toLowerCase()
          .substring(file.name.lastIndexOf("."));

        if (allowedTypes.includes(fileExtension)) {
          setTemplateFile(file);
          setOptimizationResult(null);
        } else {
          alert("Please select a .tex or .docx template file");
        }
      }
    },
    []
  );

  const handleExcelUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        const allowedTypes = [".xlsx", ".xls"];
        const fileExtension = file.name
          .toLowerCase()
          .substring(file.name.lastIndexOf("."));

        if (allowedTypes.includes(fileExtension)) {
          setExcelFile(file);
          setOptimizationResult(null);
        } else {
          alert("Please select an Excel file (.xlsx or .xls)");
        }
      }
    },
    []
  );

  const analyzeTemplate = useCallback(async () => {
    if (!templateFile || !excelFile) {
      alert("Please upload both template and Excel files");
      return;
    }

    setIsAnalyzing(true);
    const formData = new FormData();
    formData.append("template_file", templateFile);
    formData.append("excel_file", excelFile);

    try {
      const response = await fetch("/api/mvp/ai/optimize-template-with-excel", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

      const result = await response.json();
      setOptimizationResult(result);

      if (!result.success) {
        alert(`Analysis failed: ${result.error}`);
      }
    } catch (error) {
      console.error("Error analyzing template:", error);
      alert("Failed to analyze template. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }, [templateFile, excelFile]);

  const generateReport = useCallback(async () => {
    if (!templateFile || !excelFile) {
      alert("Please upload both template and Excel files");
      return;
    }

    setIsGenerating(true);
    const formData = new FormData();
    formData.append("template_file", templateFile);
    formData.append("excel_file", excelFile);

    try {
      const response = await fetch("/api/mvp/templates/generate-with-excel", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setGeneratedReport(result);
        onReportGenerated?.(result);
      } else {
        alert(`Report generation failed: ${result.error}`);
      }
    } catch (error) {
      console.error("Error generating report:", error);
      alert("Failed to generate report. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  }, [templateFile, excelFile, onReportGenerated]);

  const downloadReport = useCallback(() => {
    if (generatedReport?.downloadUrl) {
      window.open(generatedReport.downloadUrl, "_blank");
    }
  }, [generatedReport]);

  const renderOptimizationSummary = () => {
    if (!optimizationResult) return null;

    const {
      template_analysis,
      data_extraction,
      missing_fields,
      optimizations,
    } = optimizationResult;

    return (
      <div className="mt-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Analysis Results
        </h3>

        {/* Template Analysis */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">Template Structure</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium">Simple Fields:</span>
              <div className="text-blue-600">
                {template_analysis?.simple?.length || 0}
              </div>
            </div>
            <div>
              <span className="font-medium">Nested Fields:</span>
              <div className="text-blue-600">
                {template_analysis?.nested?.length || 0}
              </div>
            </div>
            <div>
              <span className="font-medium">Loop Blocks:</span>
              <div className="text-blue-600">
                {template_analysis?.loops?.length || 0}
              </div>
            </div>
            <div>
              <span className="font-medium">Tables:</span>
              <div className="text-blue-600">
                {template_analysis?.tables?.length || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Data Extraction Summary */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-800 mb-2">Data Extracted</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Participants:</span>
              <div className="text-green-600">
                {data_extraction?.participants?.length || 0}
              </div>
            </div>
            <div>
              <span className="font-medium">Program Info:</span>
              <div className="text-green-600">
                {Object.keys(data_extraction?.program_info || {}).length} fields
              </div>
            </div>
            <div>
              <span className="font-medium">Evaluation Data:</span>
              <div className="text-green-600">
                {data_extraction?.evaluation_data ? "Available" : "Not found"}
              </div>
            </div>
          </div>
        </div>

        {/* Missing Fields */}
        {missing_fields && missing_fields.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-yellow-800 mb-2 flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              Missing Data Fields ({missing_fields.length})
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              {missing_fields.map((field, index) => (
                <div
                  key={index}
                  className="text-yellow-700 bg-yellow-100 px-2 py-1 rounded"
                >
                  {field}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Optimization Suggestions */}
        {optimizations && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-medium text-purple-800 mb-2">
              Optimization Suggestions
            </h4>
            <div className="space-y-2 text-sm">
              {optimizations.missing_data_suggestions?.map(
                (suggestion: any, index: number) => (
                  <div key={index} className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-purple-700">
                        {suggestion.field}
                      </div>
                      <div className="text-purple-600">
                        {suggestion.suggestion}
                      </div>
                    </div>
                  </div>
                )
              )}

              {optimizations.template_improvements?.map(
                (improvement: any, index: number) => (
                  <div key={index} className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-purple-700">
                        {improvement.issue}
                      </div>
                      <div className="text-purple-600">
                        {improvement.suggestion}
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Enhanced Template Generator
        </h2>
        <p className="text-gray-600">
          Upload your LaTeX/Word template and Excel data file for intelligent
          report generation. The system will automatically extract all data and
          map it to your template placeholders.
        </p>
      </div>

      {/* File Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Template File Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
          <input
            type="file"
            id="template-upload"
            accept=".tex,.docx"
            onChange={handleTemplateUpload}
            className="hidden"
          />
          <label
            htmlFor="template-upload"
            className="cursor-pointer block text-center"
          >
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <div className="text-lg font-medium text-gray-700 mb-2">
              Upload Template
            </div>
            <div className="text-sm text-gray-500 mb-4">
              Drag & drop or click to select LaTeX (.tex) or Word (.docx)
              template
            </div>
            {templateFile && (
              <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm inline-block">
                {templateFile.name}
              </div>
            )}
          </label>
        </div>

        {/* Excel File Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-green-400 transition-colors">
          <input
            type="file"
            id="excel-upload"
            accept=".xlsx,.xls"
            onChange={handleExcelUpload}
            className="hidden"
          />
          <label
            htmlFor="excel-upload"
            className="cursor-pointer block text-center"
          >
            <File className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <div className="text-lg font-medium text-gray-700 mb-2">
              Upload Excel Data
            </div>
            <div className="text-sm text-gray-500 mb-4">
              Drag & drop or click to select Excel file with your data
            </div>
            {excelFile && (
              <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm inline-block">
                {excelFile.name}
              </div>
            )}
          </label>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 mb-6">
        <button
          onClick={analyzeTemplate}
          disabled={!templateFile || !excelFile || isAnalyzing}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isAnalyzing ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4" />
              Analyze Template & Data
            </>
          )}
        </button>

        <button
          onClick={generateReport}
          disabled={!templateFile || !excelFile || isGenerating}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isGenerating ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="w-4 h-4" />
              Generate Report
            </>
          )}
        </button>

        {generatedReport && (
          <button
            onClick={downloadReport}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download Report
          </button>
        )}
      </div>

      {/* Analysis Results */}
      {optimizationResult && renderOptimizationSummary()}

      {/* Generated Report Info */}
      {generatedReport && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-green-800 mb-2 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Report Generated Successfully
          </h3>
          <div className="text-sm text-green-700 space-y-1">
            <div>
              <strong>Filename:</strong> {generatedReport.filename}
            </div>
            <div>
              <strong>Missing Fields:</strong>{" "}
              {generatedReport.missing_fields?.length || 0}
            </div>
            <div>
              <strong>Context Fields:</strong>{" "}
              {Object.keys(generatedReport.context_used || {}).length}
            </div>
          </div>
          {generatedReport.optimizations && (
            <div className="mt-3 text-sm text-green-600">
              <div>✓ Template structure analyzed</div>
              <div>✓ Excel data extracted and mapped</div>
              <div>✓ Report generated with intelligent field mapping</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedTemplateEditor;
