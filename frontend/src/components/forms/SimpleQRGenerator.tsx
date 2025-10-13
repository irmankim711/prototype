import { useState } from "react";

interface SimpleQRGeneratorProps {
  formTitle: string;
  targetUrl: string;
  onClose: () => void;
}

export function SimpleQRGenerator({
  formTitle,
  targetUrl,
  onClose,
}: SimpleQRGeneratorProps) {
  const [qrCodeImage, setQrCodeImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateQR = async () => {
    setIsGenerating(true);

    try {
      // Use a simple QR code API service (like qr-server.com)
      const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(
        targetUrl
      )}`;

      setQrCodeImage(qrApiUrl);
    } catch (error) {
      console.error("Failed to generate QR code:", error);
      alert("Failed to generate QR code. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadQR = async () => {
    if (!qrCodeImage) return;

    try {
      // Fetch the image and download it
      const response = await fetch(qrCodeImage);
      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${formTitle.replace(/[^a-zA-Z0-9]/g, "_")}_QR_Code.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download QR code. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50 p-3">
      <div className="bg-white rounded-lg shadow-xl w-72 mx-auto animate-in slide-in-from-bottom-2 duration-150">
        {/* Minimal Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100">
          <span className="text-sm font-medium text-gray-900">QR Code</span>
          <button
            onClick={onClose}
            className="w-5 h-5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors flex items-center justify-center"
            aria-label="Close"
          >
            <svg
              className="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-3">
          {!qrCodeImage ? (
            <div className="text-center space-y-2">
              <p className="text-xs text-gray-600 mb-2 truncate">{formTitle}</p>
              <button
                onClick={generateQR}
                disabled={isGenerating}
                className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                {isGenerating ? (
                  <div className="flex items-center justify-center space-x-1.5">
                    <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  "Generate QR"
                )}
              </button>
            </div>
          ) : (
            <div className="text-center space-y-2">
              {/* QR Display */}
              <div className="flex justify-center">
                <div className="p-1 bg-gray-50 rounded">
                  <img
                    src={qrCodeImage}
                    alt="QR Code"
                    className="w-20 h-20"
                    crossOrigin="anonymous"
                  />
                </div>
              </div>

              <p className="text-xs text-gray-500">Scan to access</p>

              {/* Actions */}
              <div className="flex space-x-2">
                <button
                  onClick={downloadQR}
                  className="flex-1 px-2 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 transition-colors"
                >
                  Download
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 px-2 py-1.5 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SimpleQRGenerator;
