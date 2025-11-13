/**
 * DocumentPreview Component Test Suite
 * Tests for the multi-format download functionality
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import DocumentPreview from "../DocumentPreview";
import { vi } from "vitest";

// Mock axios
vi.mock("../services/axiosInstance", () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock axios for WebFetch fallback
vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
  },
}));

// Create a wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("DocumentPreview Component", () => {
  const mockOnClose = vi.fn();
  const mockOnDownload = vi.fn();
  const mockOnEdit = vi.fn();

  const mockReport = {
    id: 1,
    title: "Test Report",
    description: "Test Description",
    status: "completed",
    report_type: "custom",
    pdf_file_path: "/reports/1.pdf",
    docx_file_path: "/reports/1.docx",
    excel_file_path: "/reports/1.xlsx",
    created_at: "2025-01-01T00:00:00Z",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Download Menu Functionality", () => {
    it("should render download button when onDownload prop is provided", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        expect(downloadButton).toBeInTheDocument();
      });
    });

    it("should open download menu when download button is clicked", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Check if menu items appear
      await waitFor(() => {
        expect(screen.getByText(/Download PDF/i)).toBeInTheDocument();
        expect(screen.getByText(/Download DOCX/i)).toBeInTheDocument();
        expect(screen.getByText(/Download Excel/i)).toBeInTheDocument();
      });
    });

    it("should call onDownload with 'pdf' when PDF menu item is clicked", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Open menu
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Click PDF option
      const pdfMenuItem = await screen.findByText(/Download PDF/i);
      fireEvent.click(pdfMenuItem);

      await waitFor(() => {
        expect(mockOnDownload).toHaveBeenCalledWith("pdf");
      });
    });

    it("should call onDownload with 'docx' when DOCX menu item is clicked", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Open menu
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Click DOCX option
      const docxMenuItem = await screen.findByText(/Download DOCX/i);
      fireEvent.click(docxMenuItem);

      await waitFor(() => {
        expect(mockOnDownload).toHaveBeenCalledWith("docx");
      });
    });

    it("should call onDownload with 'excel' when Excel menu item is clicked", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Open menu
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Click Excel option
      const excelMenuItem = await screen.findByText(/Download Excel/i);
      fireEvent.click(excelMenuItem);

      await waitFor(() => {
        expect(mockOnDownload).toHaveBeenCalledWith("excel");
      });
    });

    it("should close menu after selecting a download option", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Open menu
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Click PDF option
      const pdfMenuItem = await screen.findByText(/Download PDF/i);
      fireEvent.click(pdfMenuItem);

      // Menu should be closed
      await waitFor(() => {
        expect(screen.queryByText(/Download PDF/i)).not.toBeInTheDocument();
      });
    });
  });

  describe("Available File Types Detection", () => {
    it("should show only PDF option when only PDF is available", async () => {
      const reportWithOnlyPdf = {
        ...mockReport,
        docx_file_path: null,
        excel_file_path: null,
      };

      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={reportWithOnlyPdf}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Download PDF/i)).toBeInTheDocument();
        expect(screen.queryByText(/Download DOCX/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/Download Excel/i)).not.toBeInTheDocument();
      });
    });

    it("should show only DOCX and Excel options when PDF is not available", async () => {
      const reportWithoutPdf = {
        ...mockReport,
        pdf_file_path: null,
      };

      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={reportWithoutPdf}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        expect(screen.queryByText(/Download PDF/i)).not.toBeInTheDocument();
        expect(screen.getByText(/Download DOCX/i)).toBeInTheDocument();
        expect(screen.getByText(/Download Excel/i)).toBeInTheDocument();
      });
    });

    it("should not render download button when no files are available", async () => {
      const reportWithNoFiles = {
        ...mockReport,
        pdf_file_path: null,
        docx_file_path: null,
        excel_file_path: null,
      };

      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={reportWithNoFiles}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButtons = screen.queryAllByRole("button", { name: /download/i });
        // Should not have download button in toolbar
        expect(downloadButtons.length).toBe(0);
      });
    });
  });

  describe("Integration with Preview Data", () => {
    it("should detect available files from preview data when report prop is not provided", async () => {
      const axiosInstance = await import("../services/axiosInstance");
      const mockGet = axiosInstance.default.get as ReturnType<typeof vi.fn>;

      mockGet.mockResolvedValueOnce({
        data: {
          success: true,
          preview_type: "data",
          preview_data: {
            files: {
              pdf: { exists: true, size: 1024 },
              docx: { exists: true, size: 2048 },
              excel: { exists: false },
            },
          },
        },
      });

      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Wait for preview data to load
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Should show PDF and DOCX but not Excel
      await waitFor(() => {
        expect(screen.getByText(/Download PDF/i)).toBeInTheDocument();
        expect(screen.getByText(/Download DOCX/i)).toBeInTheDocument();
        expect(screen.queryByText(/Download Excel/i)).not.toBeInTheDocument();
      });
    });
  });

  describe("Dialog Close Behavior", () => {
    it("should call onClose when close button is clicked", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const closeButton = screen.getByLabelText(/close/i);
        fireEvent.click(closeButton);
      });

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it("should reset download menu state when dialog is closed", async () => {
      const { rerender } = render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      // Open download menu
      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      // Close dialog
      rerender(
        <DocumentPreview
          open={false}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />
      );

      // Reopen dialog
      rerender(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />
      );

      // Menu should not be open
      await waitFor(() => {
        expect(screen.queryByText(/Download PDF/i)).not.toBeInTheDocument();
      });
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA attributes for download button", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        expect(downloadButton).toHaveAttribute("aria-haspopup", "true");
        expect(downloadButton).toHaveAttribute("aria-expanded", "false");
      });
    });

    it("should update aria-expanded when menu is opened", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        expect(downloadButton).toHaveAttribute("aria-expanded", "true");
      });
    });

    it("should have menu with proper ARIA role", async () => {
      render(
        <DocumentPreview
          open={true}
          onClose={mockOnClose}
          reportId={1}
          title="Test Preview"
          report={mockReport}
          onDownload={mockOnDownload}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const downloadButton = screen.getByRole("button", { name: /download/i });
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        const menu = screen.getByRole("menu");
        expect(menu).toBeInTheDocument();
      });
    });
  });
});
