import React from "react";
import PDFExportButton from "../PDFExportButton";
import ReportExportActions from "../ReportExportActions";

// Example usage of PDF export components in a report dashboard

const ReportTable: React.FC = () => {
  // Mock data - replace with real data from your API
  const reports = [
    {
      id: 1,
      title: "Customer Feedback Survey",
      description: "Q4 2024 customer satisfaction analysis",
      status: "completed",
      created_at: "2024-12-15",
      total_responses: 156,
    },
    {
      id: 2,
      title: "Employee Engagement Form",
      description: "Monthly team engagement survey",
      status: "processing",
      created_at: "2024-12-20",
      total_responses: 0,
    },
    {
      id: 3,
      title: "Product Feedback Analysis",
      description: "User feedback on new features",
      status: "error",
      created_at: "2024-12-18",
      total_responses: 45,
    },
  ];

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Reports Dashboard</h3>
        <p className="text-sm text-gray-500">
          Manage and export your form reports
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Report
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Responses
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {reports.map((report: any) => (
              <tr key={report.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {report.title}
                    </div>
                    <div className="text-sm text-gray-500">
                      {report.description}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      report.status === "completed"
                        ? "bg-green-100 text-green-800"
                        : report.status === "processing"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {report.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {report.total_responses}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {report.created_at}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <ReportExportActions
                    reportId={report.id}
                    reportTitle={report.title}
                    reportStatus={report.status}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Example usage in a single report view
const ReportDetailView: React.FC = () => {
  const report = {
    id: 1,
    title: "Customer Feedback Survey",
    description: "Q4 2024 customer satisfaction analysis",
    status: "completed",
    total_responses: 156,
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
          <p className="text-gray-600 mt-1">{report.description}</p>
        </div>

        <div className="flex space-x-2">
          {/* Full-featured PDF export button */}
          <PDFExportButton
            reportId={report.id}
            reportTitle={report.title}
            variant="button"
            size="md"
          />

          {/* Icon-only version for compact spaces */}
          <PDFExportButton
            reportId={report.id}
            reportTitle={report.title}
            variant="icon"
            size="lg"
            className="border border-gray-300 hover:border-gray-400"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {report.total_responses}
          </div>
          <div className="text-sm text-blue-800">Total Responses</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {report.status}
          </div>
          <div className="text-sm text-green-800">Status</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">4.2/5</div>
          <div className="text-sm text-purple-800">Average Rating</div>
        </div>
      </div>

      {/* Report content would go here */}
      <div className="border-t pt-6">
        <h2 className="text-lg font-semibold mb-4">Report Summary</h2>
        <p className="text-gray-600">
          This report contains detailed analysis of customer feedback collected
          through our survey form. Use the export buttons above to download the
          full report as a PDF.
        </p>
      </div>
    </div>
  );
};

export { ReportTable, ReportDetailView };
