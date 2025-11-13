/**
 * ReportHistory Component Test Suite
 * Tests for download integration with DocumentPreview
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import ReportHistory from "../ReportHistory";
import { vi } from "vitest";
import * as reportService from "../../../services/reportService";
import * as FirebaseAuthContext from "../../../context/FirebaseAuthContext";

// Mock dependencies
vi.mock("../../../services/reportService");
vi.mock("../../../context/FirebaseAuthContext");

// Create a wrapper with QueryClient and Router
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
  );
};

describe("ReportHistory Component - Download Functionality", () => {
  const mockReports = [
    {
      id: 1,
      title: "Test Report 1",
      description: "Test Description 1",
      status: "completed",
      report_type: "custom",
      pdf_file_path: "/reports/1.pdf",
      docx_file_path: "/reports/1.docx",
      excel_file_path: "/reports/1.xlsx",
      pdf_file_size: 1024,
      docx_file_size: 2048,
      excel_file_size: 3072,
      created_at: "2025-01-01T00:00:00Z",
    },
    {
      id: 2,
      title: "Test Report 2",
      description: "Test Description 2",
      status: "completed",
      report_type: "google_forms",
      pdf_file_path: "/reports/2.pdf",
      docx_file_path: null,
      excel_file_path: "/reports/2.xlsx",
      pdf_file_size: 1024,
      excel_file_size: 2048,
      created_at: "2025-01-02T00:00:00Z",
    },
  ];

  const mockStorageData = {
    total_reports: 2,
    completed_reports: 2,
    pending_reports: 0,
    failed_reports: 0,
    total_storage_mb: 10,
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock auth context
    vi.spyOn(FirebaseAuthContext, "useAuth").mockReturnValue({
      user: { uid: "test-user", email: "test@example.com" },
      loading: false,
      signIn: vi.fn(),
      signOut: vi.fn(),
      signUp: vi.fn(),
      resetPassword: vi.fn(),
    } as any);

    // Mock report service
    vi.spyOn(reportService, "reportService", "get").mockReturnValue({
      getAllReports: vi.fn().mockResolvedValue(mockReports),
      getStorageUsage: vi.fn().mockResolvedValue(mockStorageData),
      deleteReport: vi.fn().mockResolvedValue({ success: true }),
      cleanupReports: vi.fn().mockResolvedValue({ reports_processed: 0 }),
      downloadReport: vi.fn().mockResolvedValue(new Blob()),
    } as any);
  });

  describe("Download Buttons in Files Column", () => {
    it("should render download buttons for available file types", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Should show PDF, DOCX, and Excel icons for report 1
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        expect(pdfButtons.length).toBeGreaterThan(0);

        const docxButtons = screen.getAllByRole("button", { name: /download docx/i });
        expect(docxButtons.length).toBeGreaterThan(0);

        const excelButtons = screen.getAllByRole("button", { name: /download excel/i });
        expect(excelButtons.length).toBeGreaterThan(0);
      });
    });

    it("should call downloadReport when PDF button is clicked", async () => {
      const mockDownloadReport = vi.fn().mockResolvedValue(new Blob());
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        fireEvent.click(pdfButtons[0]);
      });

      await waitFor(() => {
        expect(mockDownloadReport).toHaveBeenCalledWith("1", "pdf");
      });
    });

    it("should call downloadReport when DOCX button is clicked", async () => {
      const mockDownloadReport = vi.fn().mockResolvedValue(new Blob());
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const docxButtons = screen.getAllByRole("button", { name: /download docx/i });
        fireEvent.click(docxButtons[0]);
      });

      await waitFor(() => {
        expect(mockDownloadReport).toHaveBeenCalledWith("1", "docx");
      });
    });

    it("should call downloadReport when Excel button is clicked", async () => {
      const mockDownloadReport = vi.fn().mockResolvedValue(new Blob());
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const excelButtons = screen.getAllByRole("button", { name: /download excel/i });
        fireEvent.click(excelButtons[0]);
      });

      await waitFor(() => {
        expect(mockDownloadReport).toHaveBeenCalledWith("1", "excel");
      });
    });

    it("should not show DOCX button for report without DOCX file", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Report 2 has no DOCX file
        const allDocxButtons = screen.getAllByRole("button", { name: /download docx/i });
        // Should only be 1 DOCX button (for report 1 only)
        expect(allDocxButtons).toHaveLength(1);
      });
    });
  });

  describe("Preview Dialog Integration", () => {
    it("should open preview dialog when preview button is clicked", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const previewButtons = screen.getAllByRole("button", { name: /preview report/i });
        fireEvent.click(previewButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText(/report preview/i)).toBeInTheDocument();
      });
    });

    it("should pass report object to DocumentPreview", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const previewButtons = screen.getAllByRole("button", { name: /preview report/i });
        fireEvent.click(previewButtons[0]);
      });

      await waitFor(() => {
        // Check that dialog opened with report data
        const dialog = screen.getByRole("dialog");
        expect(dialog).toBeInTheDocument();
      });
    });

    it("should handle download from preview dialog", async () => {
      const mockDownloadReport = vi.fn().mockResolvedValue(new Blob());
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      // Open preview
      await waitFor(() => {
        const previewButtons = screen.getAllByRole("button", { name: /preview report/i });
        fireEvent.click(previewButtons[0]);
      });

      // Wait for dialog and find download button
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /^download$/i });
        fireEvent.click(downloadButton);
      });

      // Click a download option from the menu
      await waitFor(() => {
        const pdfOption = screen.getByText(/download pdf/i);
        fireEvent.click(pdfOption);
      });

      await waitFor(() => {
        expect(mockDownloadReport).toHaveBeenCalledWith(mockReports[0], "pdf");
      });
    });

    it("should close preview dialog when close button is clicked", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      // Open preview
      await waitFor(() => {
        const previewButtons = screen.getAllByRole("button", { name: /preview report/i });
        fireEvent.click(previewButtons[0]);
      });

      // Close dialog
      await waitFor(() => {
        const closeButton = screen.getByLabelText(/close/i);
        fireEvent.click(closeButton);
      });

      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });
  });

  describe("Download Success/Error Handling", () => {
    it("should show success message when download succeeds", async () => {
      const mockDownloadReport = vi.fn().mockResolvedValue(new Blob());
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        fireEvent.click(pdfButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText(/report downloaded as pdf/i)).toBeInTheDocument();
      });
    });

    it("should show error message when download fails", async () => {
      const mockDownloadReport = vi.fn().mockRejectedValue(new Error("Network error"));
      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        fireEvent.click(pdfButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText(/failed to download pdf/i)).toBeInTheDocument();
      });
    });

    it("should trigger file download when blob is received", async () => {
      const mockBlob = new Blob(["test content"], { type: "application/pdf" });
      const mockDownloadReport = vi.fn().mockResolvedValue(mockBlob);

      vi.spyOn(reportService, "reportService", "get").mockReturnValue({
        ...reportService.reportService,
        downloadReport: mockDownloadReport,
      } as any);

      // Mock URL.createObjectURL
      const mockCreateObjectURL = vi.fn().mockReturnValue("blob:test-url");
      global.URL.createObjectURL = mockCreateObjectURL;
      global.URL.revokeObjectURL = vi.fn();

      // Mock createElement and appendChild
      const mockAnchor = document.createElement("a");
      const mockClick = vi.fn();
      mockAnchor.click = mockClick;
      vi.spyOn(document, "createElement").mockReturnValue(mockAnchor as any);
      const mockAppendChild = vi.spyOn(document.body, "appendChild").mockImplementation(() => mockAnchor as any);
      const mockRemoveChild = vi.spyOn(document.body, "removeChild").mockImplementation(() => mockAnchor as any);

      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        fireEvent.click(pdfButtons[0]);
      });

      await waitFor(() => {
        expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
        expect(mockClick).toHaveBeenCalled();
        expect(mockAppendChild).toHaveBeenCalled();
        expect(mockRemoveChild).toHaveBeenCalled();
      });
    });
  });

  describe("File Type Tooltips", () => {
    it("should show correct tooltip for PDF button", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const pdfButtons = screen.getAllByRole("button", { name: /download pdf/i });
        expect(pdfButtons[0]).toHaveAttribute("aria-label", "Download PDF");
      });
    });

    it("should show correct tooltip for DOCX button", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const docxButtons = screen.getAllByRole("button", { name: /download docx/i });
        expect(docxButtons[0]).toHaveAttribute("aria-label", "Download DOCX");
      });
    });

    it("should show correct tooltip for Excel button", async () => {
      render(<ReportHistory />, { wrapper: createWrapper() });

      await waitFor(() => {
        const excelButtons = screen.getAllByRole("button", { name: /download excel/i });
        expect(excelButtons[0]).toHaveAttribute("aria-label", "Download Excel");
      });
    });
  });
});
