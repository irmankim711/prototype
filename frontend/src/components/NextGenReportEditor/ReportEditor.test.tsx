/**
 * NextGen Report Editor Tests
 * Basic integration tests for the report editor components
 */

import React from 'react';

import { render, screen, fireEvent, waitFor  } from '@testing-library/react';

import { ThemeProvider, createTheme  } from '@mui/material/styles';

import ReportEditor from './ReportEditor';

import type { EditorContent } from './ReportEditor';

// Mock the services
jest.mock('../../services/enhancedReportService', () => ({
  autoSaveReport: jest.fn().mockResolvedValue({}),
  updateReportContent: jest.fn().mockResolvedValue({ id: 1, version_number: 1 }),
  getReportVersions: jest.fn().mockResolvedValue({ versions: [], report_name: 'Test Report', total_versions: 0 }),
}));

jest.mock('../../services/collaborationService', () => ({
  createCollaborationSession: jest.fn().mockReturnValue({
    id: 'session-1',
    participants: [{ id: 'user-1', name: 'Test User' }],
  }),
}));

// Mock socket.io-client
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
  })),
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ReportEditor', () => {
  const mockInitialContent: EditorContent = {
    title: 'Test Report',
    content: '<p>Test content</p>',
    sections: [],
    metadata: {
      wordCount: 2,
      characterCount: 20,
      lastModified: new Date(),
      version: 1,
    },
  };

const defaultProps = {
    reportId: 1,
    initialContent: mockInitialContent,
    onSave: jest.fn(),
    onClose: jest.fn(),
  };

beforeEach(() => {
    jest.clearAllMocks();
  });

it('renders the report editor with initial content', () => {
    renderWithTheme(<ReportEditor {...defaultProps} />);

expect(screen.getByDisplayValue('Test Report')).toBeInTheDocument();
    
expect(screen.getByText('1 user')).toBeInTheDocument();
  });

it('shows save button when there are unsaved changes', async () => {
    renderWithTheme(<ReportEditor {...defaultProps} />);
    
    // The save button should be disabled initially (no unsaved changes)
    const saveButton = screen.getByRole('button', { name: /save/i });
    
expect(saveButton).toBeDisabled();
  });

it('displays auto-save indicator', () => {
    renderWithTheme(<ReportEditor {...defaultProps} />);
    
    // Should show some save status indicator
    expect(screen.getByText(/saved|not saved|unsaved/i)).toBeInTheDocument();
  });

it('opens version history panel', async () => {
    renderWithTheme(<ReportEditor {...defaultProps} showVersionHistory={true} />);

const historyButton = screen.getByRole('button', { name: /version history/i });
    
fireEvent.click(historyButton);

await waitFor(() => {
      expect(screen.getByText('Version History')).toBeInTheDocument();
    });
  });

it('handles read-only mode', () => {
    renderWithTheme(<ReportEditor {...defaultProps} readOnly={true} />);
    
    // Save button should not be present in read-only mode
    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
  });

it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn();
    
renderWithTheme(<ReportEditor {...defaultProps} onClose={onClose} />);

const closeButton = screen.getByRole('button', { name: /close editor/i });
    
fireEvent.click(closeButton);

expect(onClose).toHaveBeenCalled();
  });

it('displays collaboration indicators when enabled', () => {
    renderWithTheme(<ReportEditor {...defaultProps} enableCollaboration={true} />);

expect(screen.getByText('1 user')).toBeInTheDocument();
  });

it('hides collaboration features when disabled', () => {
    renderWithTheme(<ReportEditor {...defaultProps} enableCollaboration={false} />);

expect(screen.queryByText(/user/)).not.toBeInTheDocument();
  });
});

describe('AutoSaveIndicator', () => {
  it('shows saving state', () => {
    import { AutoSaveIndicator  } from './AutoSaveIndicator';

renderWithTheme(
      <AutoSaveIndicator
        isSaving={true}
        isAutoSaving={false}
        hasUnsavedChanges={false}
        lastSaved={null}
      />
    );

expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

it('shows auto-saving state', () => {
    import { AutoSaveIndicator  } from './AutoSaveIndicator';

renderWithTheme(
      <AutoSaveIndicator
        isSaving={false}
        isAutoSaving={true}
        hasUnsavedChanges={false}
        lastSaved={null}
      />
    );

expect(screen.getByText('Auto-saving...')).toBeInTheDocument();
  });

it('shows unsaved changes state', () => {
    import { AutoSaveIndicator  } from './AutoSaveIndicator';

renderWithTheme(
      <AutoSaveIndicator
        isSaving={false}
        isAutoSaving={false}
        hasUnsavedChanges={true}
        lastSaved={null}
      />
    );

expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });

it('shows saved state with timestamp', () => {
    import { AutoSaveIndicator  } from './AutoSaveIndicator';
    
const lastSaved = new Date();

renderWithTheme(
      <AutoSaveIndicator
        isSaving={false}
        isAutoSaving={false}
        hasUnsavedChanges={false}
        lastSaved={lastSaved}
      />
    );

expect(screen.getByText('Saved')).toBeInTheDocument();
  });
});
