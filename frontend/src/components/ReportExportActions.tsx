import React from "react";
import { FileText, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import PDFExportButton from "./PDFExportButton";

interface ReportExportActionsProps {
  reportId: number;
  reportTitle: string;
  reportStatus?: string;
  className?: string;
}

const ReportExportActions: React.FC<ReportExportActionsProps> = ({
  reportId,
  reportTitle,
  reportStatus = "completed",
  className = "",
}) => {
  const isExportable = reportStatus === "completed" || reportStatus === "ready";

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {/* PDF Export Button */}
      <PDFExportButton
        reportId={reportId}
        reportTitle={reportTitle}
        variant="icon"
        size="sm"
        className={!isExportable ? "opacity-50 cursor-not-allowed" : ""}
      />

      {/* Other export options can be added here */}
      <button
        className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
        title="Export as Excel (Coming Soon)"
        disabled
      >
        <FileText size={16} />
      </button>

      {/* Status indicator */}
      <div className="flex items-center space-x-1">
        {reportStatus === "completed" && (
          <div title="Report ready for export">
            <CheckCircle size={14} className="text-green-500" />
          </div>
        )}
        {reportStatus === "processing" && (
          <div title="Report processing">
            <Loader2 size={14} className="text-blue-500 animate-spin" />
          </div>
        )}
        {reportStatus === "error" && (
          <div title="Report generation failed">
            <AlertCircle size={14} className="text-red-500" />
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportExportActions;
