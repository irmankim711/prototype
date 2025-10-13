import React from "react";
import { useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";

interface PDFExportButtonProps {
  reportId: number;
  reportTitle?: string;
  className?: string;
  variant?: "button" | "icon" | "link";
  size?: "sm" | "md" | "lg";
}

const PDFExportButton: React.FC<PDFExportButtonProps> = ({
  reportId,
  reportTitle = "Report",
  className = "",
  variant = "button",
  size = "md",
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportToPDF = async () => {
    setIsExporting(true);
    setError(null);

    try {
      // Get authentication token
      const token =
        localStorage.getItem("token") || sessionStorage.getItem("token");

      if (!token) {
        throw Error("Authentication required. Please log in.");
      }

      // Make API request to export PDF
      const response = await fetch(`/api/reports/export/pdf/${reportId}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw Error(
          errorData.error ||
            `Export failed: ${response.status} ${response.statusText}`
        );
      }

      // Check if response is actually a PDF
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/pdf")) {
        throw Error("Invalid response format. Expected PDF file.");
      }

      // Get the PDF blob
      const blob = await response.blob();
      if (blob.size === 0) {
        throw Error("Received empty PDF file.");
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Generate filename
      const timestamp = new Date()
        .toISOString()
        .slice(0, 19)
        .replace(/[:.]/g, "-");
      const filename = `${reportTitle.replace(
        /[^a-zA-Z0-9]/g,
        "_"
      )}_${timestamp}.pdf`;
      link.download = filename;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(url);

      // Show success message (you can customize this)
      console.log(`✅ PDF exported successfully: ${filename}`);
    } catch (error) {
      console.error("PDF export error:", error);
      setError(error instanceof Error ? error.message : "Failed to export PDF");
    } finally {
      setIsExporting(false);
    }
  };

  // Base styles for different variants
  const getButtonStyles = () => {
    const baseStyles =
      "inline-flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";

    const sizeStyles = {
      sm: "px-2 py-1 text-xs",
      md: "px-3 py-2 text-sm",
      lg: "px-4 py-2 text-base",
    };

    const variantStyles = {
      button:
        "bg-blue-600 hover:bg-blue-700 text-white rounded-md shadow-sm focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed",
      icon: "p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded-full focus:ring-blue-500",
      link: "text-blue-600 hover:text-blue-800 underline focus:ring-blue-500",
    };

    return `${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`;
  };

  const getIconSize = () => {
    return size === "sm" ? 14 : size === "lg" ? 20 : 16;
  };

  const renderContent = () => {
    if (isExporting) {
      return (
        <>
          <Loader2 className="animate-spin" size={getIconSize()} />
          {variant === "button" && <span className="ml-2">Exporting...</span>}
        </>
      );
    }

    switch (variant) {
      case "icon":
        return <FileText size={getIconSize()} />;
      case "link":
        return (
          <>
            <Download size={getIconSize()} />
            <span className="ml-1">Export PDF</span>
          </>
        );
      default:
        return (
          <>
            <Download size={getIconSize()} />
            <span className="ml-2">Export PDF</span>
          </>
        );
    }
  };

  return (
    <div className="relative">
      <button
        onClick={exportToPDF}
        disabled={isExporting}
        className={getButtonStyles()}
        title={`Export ${reportTitle} as PDF`}
        aria-label={`Export ${reportTitle} as PDF`}
      >
        {renderContent()}
      </button>

      {error && (
        <div className="absolute top-full left-0 mt-1 p-2 bg-red-100 border border-red-300 rounded-md shadow-lg z-10 min-w-max">
          <p className="text-red-700 text-xs">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700 text-xs underline mt-1"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default PDFExportButton;
