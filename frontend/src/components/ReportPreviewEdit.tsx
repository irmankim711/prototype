import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import EnhancedReportEditor from './EnhancedReportEditor';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface ReportData {
  id: number;
  title: string;
  description: string;
  status: string;
  generation_progress: number;
  generated_data: any;
  report_config: any;
  pdf_download_url?: string;
  docx_download_url?: string;
  excel_download_url?: string;
  file_sizes?: {
    pdf?: number;
    docx?: number;
    excel?: number;
  };
}

interface ReportPreviewEditProps {
  reportId: number;
  onClose: () => void;
  onReportUpdated: (reportId: number) => void;
}

const ReportPreviewEdit: React.FC<ReportPreviewEditProps> = ({
  reportId,
  onClose,
  onReportUpdated
}) => {
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'edit' | 'downloads'>('preview');
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [showEnhancedEditor, setShowEnhancedEditor] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchReportData();
  }, [reportId]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/reports/${reportId}/preview`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setReport(data.preview);
        setEditData(data.preview.generated_data);
      } else {
        setError(data.error || 'Failed to fetch report data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
    setActiveTab('edit');
  };

  const handleSave = async () => {
    if (!editData) return;

    try {
      setRegenerating(true);
      const response = await fetch(`/api/reports/${reportId}/edit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          generated_data: editData
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setEditing(false);
        setActiveTab('preview');
        // Refresh report data
        await fetchReportData();
        onReportUpdated(reportId);
      } else {
        setError(data.error || 'Failed to update report');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setRegenerating(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setEditData(report?.generated_data);
    setActiveTab('preview');
  };

  const handleDownload = async (fileType: 'pdf' | 'docx' | 'excel') => {
    try {
      const response = await fetch(`/api/reports/${reportId}/download/${fileType}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report?.title || 'report'}.${fileType}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md">
          <div className="text-red-600 text-center mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error</h3>
          <p className="text-gray-600 mb-4">{error || 'Report not found'}</p>
          <button
            onClick={onClose}
            className="w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-11/12 h-5/6 max-w-7xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{report.title}</h2>
            <p className="text-gray-600">{report.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            {report.status === 'completed' && (
              <>
                <button
                  onClick={() => setShowEnhancedEditor(true)}
                  className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 011-1h1a2 2 0 100-4H7a1 1 0 01-1-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                  </svg>
                  AI Editor
                </button>
                <button
                  onClick={handleEdit}
                  disabled={editing}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {editing ? 'Editing...' : 'Edit Report'}
                </button>
                <button
                  onClick={onClose}
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                >
                  Close
                </button>
              </>
            )}
          </div>
        </div>

        {/* Status Bar */}
        {report.status === 'generating' && (
          <div className="bg-blue-50 p-4 border-b">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span className="text-blue-800">Generating report... {report.generation_progress}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${report.generation_progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('preview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'preview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Preview
            </button>
            <button
              onClick={() => setActiveTab('edit')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'edit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Edit Data
            </button>
            <button
              onClick={() => setActiveTab('downloads')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'downloads'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Downloads
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'preview' && (
            <div className="space-y-6">
              {report.status === 'completed' ? (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Report Preview</h3>
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-900">Report Information</h4>
                      <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                        <div>
                          <span className="font-medium">Title:</span> {report.title}
                        </div>
                        <div>
                          <span className="font-medium">Status:</span> {report.status}
                        </div>
                        <div>
                          <span className="font-medium">Generated Data:</span> {JSON.stringify(report.generated_data).substring(0, 100)}...
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Report is being generated...</p>
                  <p className="text-sm text-gray-500 mt-2">Progress: {report.generation_progress}%</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'edit' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Edit Report Data</h3>
                <div className="space-x-3">
                  <button
                    onClick={handleCancel}
                    className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={regenerating}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    {regenerating ? 'Regenerating...' : 'Save & Regenerate'}
                  </button>
                </div>
              </div>

              <div className="border rounded-lg p-4">
                <textarea
                  value={JSON.stringify(editData, null, 2)}
                  onChange={(e) => {
                    try {
                      setEditData(JSON.parse(e.target.value));
                    } catch (err) {
                      // Invalid JSON, keep the text as is
                    }
                  }}
                  className="w-full h-96 font-mono text-sm border rounded p-3"
                  placeholder="Edit JSON data here..."
                />
              </div>

              {regenerating && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <span className="text-blue-800">Regenerating report...</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'downloads' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">Download Reports</h3>
              
              {report.status === 'completed' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* PDF Download */}
                  <div className="border rounded-lg p-6 text-center">
                    <div className="text-red-600 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">PDF Report</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      {report.file_sizes?.pdf ? formatFileSize(report.file_sizes.pdf) : 'Unknown size'}
                    </p>
                    <button
                      onClick={() => handleDownload('pdf')}
                      className="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                    >
                      Download PDF
                    </button>
                  </div>

                  {/* DOCX Download */}
                  <div className="border rounded-lg p-6 text-center">
                    <div className="text-blue-600 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">Word Document</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      {report.file_sizes?.docx ? formatFileSize(report.file_sizes.docx) : 'Unknown size'}
                    </p>
                    <button
                      onClick={() => handleDownload('docx')}
                      className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                      Download DOCX
                    </button>
                  </div>

                  {/* Excel Download */}
                  <div className="border rounded-lg p-6 text-center">
                    <div className="text-green-600 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">Excel Spreadsheet</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      {report.file_sizes?.excel ? formatFileSize(report.file_sizes.excel) : 'Unknown size'}
                    </p>
                    <button
                      onClick={() => handleDownload('excel')}
                      className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                    >
                      Download Excel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <p className="text-gray-600">Reports are not ready for download yet</p>
                  <p className="text-sm text-gray-500 mt-2">Please wait for generation to complete</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Enhanced Report Editor Modal */}
      {showEnhancedEditor && (
        <EnhancedReportEditor
          reportId={reportId}
          onClose={() => setShowEnhancedEditor(false)}
          onReportUpdated={(id) => {
            setShowEnhancedEditor(false);
            onReportUpdated(id);
            fetchReportData(); // Refresh report data
          }}
        />
      )}
    </div>
  );
};

export default ReportPreviewEdit;
