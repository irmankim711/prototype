import { useState } from "react";
import QRCodeGenerator from "./QRCodeGenerator";
import QRCodeModal from "./QRCodeModal";

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

interface FormQRManagerProps {
  formId: number;
  formTitle: string;
  existingQRCodes?: QRCodeData[];
}

export function FormQRManager({
  formId,
  formTitle,
  existingQRCodes = [],
}: FormQRManagerProps) {
  const [showGenerator, setShowGenerator] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedQRCode, setSelectedQRCode] = useState<QRCodeData | null>(null);
  const [qrCodes, setQRCodes] = useState<QRCodeData[]>(existingQRCodes);

  const handleQRCodeGenerated = (newQRCode: QRCodeData) => {
    setQRCodes((prev) => [...prev, newQRCode]);
    setSelectedQRCode(newQRCode);
    setShowModal(true);
  };

  const handleViewQRCode = (qrCode: QRCodeData) => {
    setSelectedQRCode(qrCode);
    setShowModal(true);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          QR Codes for {formTitle}
        </h3>
        <button
          onClick={() => setShowGenerator(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <svg
            className="w-4 h-4 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Generate QR Code
        </button>
      </div>

      {/* QR Codes List */}
      {qrCodes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {qrCodes.map((qrCode) => (
            <div
              key={qrCode.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* QR Code Preview */}
              <div className="flex justify-center mb-3">
                <img
                  src={qrCode.data_url}
                  alt={qrCode.title}
                  className="w-24 h-24 border border-gray-200 rounded"
                />
              </div>

              {/* QR Code Info */}
              <div className="text-center space-y-2">
                <h4
                  className="font-medium text-gray-900 truncate"
                  title={qrCode.title}
                >
                  {qrCode.title}
                </h4>
                {qrCode.description && (
                  <p
                    className="text-sm text-gray-600 truncate"
                    title={qrCode.description}
                  >
                    {qrCode.description}
                  </p>
                )}

                {/* Stats */}
                <div className="flex justify-center space-x-4 text-xs text-gray-500">
                  <span>{qrCode.settings.size}px</span>
                  <span>Level {qrCode.settings.error_correction}</span>
                </div>

                {/* Actions */}
                <div className="flex space-x-2 pt-2">
                  <button
                    onClick={() => handleViewQRCode(qrCode)}
                    className="flex-1 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                  >
                    View & Download
                  </button>
                  <button
                    onClick={() => navigator.clipboard.writeText(qrCode.url)}
                    className="flex-1 px-3 py-1.5 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors"
                  >
                    Copy URL
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M12 4.5V3m0 1.5V6m0-1.5h1.5m-1.5 0H9m0 0L7.5 4.5M9 3l1.5 1.5M9 6l1.5-1.5m0 0L12 6m-1.5-1.5L9 6m1.5-1.5L12 3m-1.5 1.5V6m0-1.5h1.5m-1.5 0H9"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No QR codes yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Generate your first QR code to make this form easily accessible.
          </p>
          <button
            onClick={() => setShowGenerator(true)}
            className="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Generate QR Code
          </button>
        </div>
      )}

      {/* QR Code Generator Modal */}
      {showGenerator && (
        <QRCodeGenerator
          formId={formId}
          formTitle={formTitle}
          onQRCodeGenerated={handleQRCodeGenerated}
          onClose={() => setShowGenerator(false)}
        />
      )}

      {/* QR Code View Modal */}
      {showModal && selectedQRCode && (
        <QRCodeModal
          qrCode={selectedQRCode}
          onClose={() => {
            setShowModal(false);
            setSelectedQRCode(null);
          }}
        />
      )}
    </div>
  );
}

export default FormQRManager;
