import { useState } from "react";

interface QRCodeModalProps {
  qrCode: {
    id: number;
    data_url: string;
    url: string;
    title: string;
    description: string;
    settings: {
      size: number;
      error_correction: string;
      border: number;
      background_color: string;
      foreground_color: string;
    };
  };
  onClose: () => void;
}

export function QRCodeModal({ onClose, qrCode }: QRCodeModalProps) {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "error">(
    "idle"
  );

  const downloadQRCode = () => {
    try {
      // Create a temporary link element
      const link = document.createElement("a");
      link.href = qrCode.data_url;
      link.download = `${qrCode.title.replace(
        /[^a-zA-Z0-9]/g,
        "_"
      )}_QR_Code.png`;

      // Append to body and click
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      console.log("QR code downloaded successfully");
    } catch (error) {
      console.error("Failed to download QR code:", error);
    }
  };

  const copyQRCodeData = async () => {
    try {
      await navigator.clipboard.writeText(qrCode.data_url);
      setCopyStatus("copied");
      setTimeout(() => setCopyStatus("idle"), 2000);
    } catch (error) {
      console.error("Failed to copy QR code data:", error);
      setCopyStatus("error");
      setTimeout(() => setCopyStatus("idle"), 2000);
    }
  };

  const copyURL = async () => {
    try {
      await navigator.clipboard.writeText(qrCode.url);
      setCopyStatus("copied");
      setTimeout(() => setCopyStatus("idle"), 2000);
    } catch (error) {
      console.error("Failed to copy URL:", error);
      setCopyStatus("error");
      setTimeout(() => setCopyStatus("idle"), 2000);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {qrCode.title}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Close modal"
              aria-label="Close modal"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          {qrCode.description && (
            <p className="text-gray-600 mt-2">{qrCode.description}</p>
          )}
        </div>

        <div className="p-6 space-y-6">
          {/* QR Code Display */}
          <div className="flex justify-center">
            <div
              className="relative group cursor-pointer border rounded-lg shadow-sm overflow-hidden"
              onClick={downloadQRCode}
            >
              <img
                src={qrCode.data_url}
                alt="QR Code"
                className="w-full h-auto"
              />
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div className="text-white font-medium text-sm">
                  Click to download
                </div>
              </div>
            </div>
          </div>

          {/* URL Display */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Target URL:
            </label>
            <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded border">
              <code className="flex-1 text-sm text-gray-800 break-all">
                {qrCode.url}
              </code>
              <button
                onClick={copyURL}
                className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
                title="Copy URL"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* QR Code Settings */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              QR Code Settings:
            </label>
            <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
              <div>Size: {qrCode.settings.size}px</div>
              <div>Error Correction: {qrCode.settings.error_correction}</div>
              <div>Border: {qrCode.settings.border}px</div>
              <div className="flex items-center space-x-2">
                <span>Colors:</span>
                <span
                  className="text-xs bg-gray-100 px-2 py-1 rounded"
                  title="Foreground Color"
                >
                  {qrCode.settings.foreground_color}
                </span>
                <span
                  className="text-xs bg-gray-100 px-2 py-1 rounded"
                  title="Background Color"
                >
                  {qrCode.settings.background_color}
                </span>
              </div>
            </div>
          </div>

          {/* Copy Status */}
          {copyStatus !== "idle" && (
            <div
              className={`text-sm text-center p-2 rounded ${
                copyStatus === "copied"
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {copyStatus === "copied"
                ? "Copied to clipboard!"
                : "Failed to copy"}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <button
              onClick={downloadQRCode}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span>Download PNG</span>
            </button>
            <button
              onClick={copyQRCodeData}
              className="flex-1 bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <span>Copy Data</span>
            </button>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default QRCodeModal;
