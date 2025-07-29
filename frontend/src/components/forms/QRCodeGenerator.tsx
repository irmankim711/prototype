import { useState } from "react";
import { formBuilderAPI } from "../../services/formBuilder";

interface QRCodeData {
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
}

interface QRCodeGeneratorProps {
  formId: number;
  formTitle: string;
  onQRCodeGenerated: (qrCode: QRCodeData) => void;
  onClose: () => void;
  defaultUrl?: string;
}

export function QRCodeGenerator({
  formId,
  formTitle,
  onQRCodeGenerated,
  onClose,
  defaultUrl,
}: QRCodeGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [qrCode, setQrCode] = useState<QRCodeData | null>(null);

  const generateQR = async () => {
    setIsGenerating(true);

    try {
      const qrData = {
        external_url: defaultUrl || `${window.location.origin}/forms/${formId}`,
        title: `QR Code for ${formTitle}`,
        description: `Scan to access ${formTitle}`,
        size: 300,
        error_correction: "M",
        border: 4,
        background_color: "#FFFFFF",
        foreground_color: "#000000",
      };

      console.log("Creating QR code with data:", qrData);
      console.log("Form ID:", formId);

      const response = await formBuilderAPI.createFormQRCode(formId, qrData);
      console.log("QR code response:", response);

      setQrCode(response.qr_code);
      onQRCodeGenerated(response.qr_code);
    } catch (error: unknown) {
      console.error("Failed to generate QR code:", error);

      const axiosError = error as {
        response?: { data?: { error?: string }; status?: number };
      };
      console.error("Error response:", axiosError.response?.data);
      console.error("Error status:", axiosError.response?.status);

      let errorMessage = "Failed to generate QR code. ";
      if (axiosError.response?.status === 401) {
        errorMessage += "Please login first.";
      } else if (axiosError.response?.status === 404) {
        errorMessage += "Form not found.";
      } else if (axiosError.response?.data?.error) {
        errorMessage += axiosError.response.data.error;
      } else {
        errorMessage += "Please try again.";
      }

      alert(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadQR = () => {
    if (!qrCode) return;

    try {
      const link = document.createElement("a");
      link.href = qrCode.data_url;
      link.download = `${formTitle.replace(/[^a-zA-Z0-9]/g, "_")}_QR_Code.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download QR code. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              QR Code for {formTitle}
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
        </div>

        <div className="p-6 text-center">
          {!qrCode ? (
            // Generate QR Code Button
            <div className="space-y-4">
              <p className="text-gray-600">
                Generate a QR code for easy access to your form
              </p>
              <button
                onClick={generateQR}
                disabled={isGenerating}
                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg font-medium"
              >
                {isGenerating ? "Generating..." : "Generate QR Code"}
              </button>
            </div>
          ) : (
            // Show QR Code
            <div className="space-y-4">
              <div className="flex justify-center">
                <img
                  src={qrCode.data_url}
                  alt="QR Code"
                  className="border rounded-lg shadow-sm"
                />
              </div>

              <p className="text-sm text-gray-600">
                Scan this QR code to access the form
              </p>

              <div className="flex space-x-3">
                <button
                  onClick={downloadQR}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
                >
                  Download PNG
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
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

export default QRCodeGenerator;
