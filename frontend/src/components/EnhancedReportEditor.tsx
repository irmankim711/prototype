import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface ReportData {
  id: number;
  title: string;
  description: string;
  report_type: string;
  status: string;
  created_at: string;
  latex_content: string;
  file_path: string;
}

interface AISuggestion {
  category: string;
  suggestion: string;
  importance: 'high' | 'medium' | 'low';
}

interface EnhancementResult {
  success: boolean;
  original_text: string;
  enhanced_text?: string;
  translated_text?: string;
  enhancement_type: string;
  ai_powered: boolean;
  message?: string;
}

interface SuggestionsResult {
  success: boolean;
  suggestions: AISuggestion[];
  context: string;
  ai_powered: boolean;
  message?: string;
}

interface EnhancedReportEditorProps {
  reportId: number;
  onClose: () => void;
  onReportUpdated: (reportId: number) => void;
}

const EnhancedReportEditor: React.FC<EnhancedReportEditorProps> = ({
  reportId,
  onClose,
  onReportUpdated
}) => {
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'edit' | 'preview' | 'ai-tools'>('edit');
  const [latexContent, setLatexContent] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [aiSuggestions, setAISuggestions] = useState<AISuggestion[]>([]);
  const [enhancementResult, setEnhancementResult] = useState<EnhancementResult | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [processingAI, setProcessingAI] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [cursorPosition, setCursorPosition] = useState({ start: 0, end: 0 });

  useEffect(() => {
    fetchReportData();
  }, [reportId]);

  // Auto-save functionality
  useEffect(() => {
    const autoSaveInterval = setInterval(() => {
      if (latexContent && latexContent !== report?.latex_content) {
        handleAutoSave();
      }
    }, 30000); // Auto-save every 30 seconds

    return () => clearInterval(autoSaveInterval);
  }, [latexContent, report?.latex_content]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/nextgen/reports/${reportId}/view`, {
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
        setReport(data.report);
        setLatexContent(data.report.latex_content);
      } else {
        setError(data.error || 'Failed to fetch report data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSave = async () => {
    if (!latexContent || saving) return;

    try {
      const response = await fetch(`/api/v1/nextgen/reports/${reportId}/edit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latex_content: latexContent
        })
      });

      if (response.ok) {
        console.log('Auto-saved successfully');
      }
    } catch (err) {
      console.error('Auto-save failed:', err);
    }
  };

  const handleSave = async () => {
    if (!latexContent || saving) return;

    try {
      setSaving(true);
      const response = await fetch(`/api/v1/nextgen/reports/${reportId}/edit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latex_content: latexContent
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        onReportUpdated(reportId);
        // Update report state
        if (report) {
          setReport({
            ...report,
            latex_content: latexContent
          });
        }
      } else {
        setError(data.error || 'Failed to save report');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleTextSelection = () => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart;
      const end = textareaRef.current.selectionEnd;
      const selected = latexContent.substring(start, end);
      
      setSelectedText(selected);
      setCursorPosition({ start, end });
    }
  };

  const enhanceTextWithAI = async (type: string) => {
    if (!selectedText.trim()) {
      alert('Please select text to enhance');
      return;
    }

    try {
      setProcessingAI(true);
      const response = await fetch('/api/v1/nextgen/ai/enhance-text', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: selectedText,
          type: type,
          context: 'report'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: EnhancementResult = await response.json();
      setEnhancementResult(data);

      if (data.success && data.enhanced_text) {
        // Option to apply the enhancement
        if (confirm('Apply AI enhancement to selected text?')) {
          applyEnhancement(data.enhanced_text);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI enhancement failed');
    } finally {
      setProcessingAI(false);
    }
  };

  const translateText = async (targetLanguage: string) => {
    if (!selectedText.trim()) {
      alert('Please select text to translate');
      return;
    }

    try {
      setProcessingAI(true);
      const response = await fetch('/api/v1/nextgen/ai/translate-text', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: selectedText,
          target_language: targetLanguage,
          source_language: 'auto'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.success && data.translated_text) {
        if (confirm(`Apply translation to ${targetLanguage}?`)) {
          applyEnhancement(data.translated_text);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setProcessingAI(false);
    }
  };

  const applyEnhancement = (enhancedText: string) => {
    const newContent = latexContent.substring(0, cursorPosition.start) + 
                      enhancedText + 
                      latexContent.substring(cursorPosition.end);
    setLatexContent(newContent);
    
    // Clear selection
    setSelectedText('');
    setEnhancementResult(null);
  };

  const getAISuggestions = async () => {
    if (!latexContent.trim()) {
      alert('Please add some content first');
      return;
    }

    try {
      setLoadingSuggestions(true);
      const response = await fetch('/api/v1/nextgen/ai/suggestions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: latexContent,
          context: 'report'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SuggestionsResult = await response.json();
      if (data.success) {
        setAISuggestions(data.suggestions);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get suggestions');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const insertAtCursor = (textToInsert: string) => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart;
      const end = textareaRef.current.selectionEnd;
      const newContent = latexContent.substring(0, start) + textToInsert + latexContent.substring(end);
      setLatexContent(newContent);
      
      // Set cursor position after inserted text
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + textToInsert.length;
          textareaRef.current.focus();
        }
      }, 0);
    }
  };

  const formatText = (type: string) => {
    if (!selectedText) {
      alert('Please select text to format');
      return;
    }

    let formatted = '';
    switch (type) {
      case 'bold':
        formatted = `\\textbf{${selectedText}}`;
        break;
      case 'italic':
        formatted = `\\textit{${selectedText}}`;
        break;
      case 'underline':
        formatted = `\\underline{${selectedText}}`;
        break;
      case 'section':
        formatted = `\\section{${selectedText}}`;
        break;
      case 'subsection':
        formatted = `\\subsection{${selectedText}}`;
        break;
      default:
        return;
    }

    applyEnhancement(formatted);
  };

  const hasUnsavedChanges = useMemo(() => {
    return latexContent !== report?.latex_content;
  }, [latexContent, report?.latex_content]);

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
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              {report.title}
              {hasUnsavedChanges && (
                <span className="ml-2 text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                  Unsaved changes
                </span>
              )}
            </h2>
            <p className="text-gray-600">{report.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleSave}
              disabled={saving || !hasUnsavedChanges}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={onClose}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('edit')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'edit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Edit Content
            </button>
            <button
              onClick={() => setActiveTab('ai-tools')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'ai-tools'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              AI Tools
            </button>
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
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {activeTab === 'edit' && (
            <div className="h-full flex">
              {/* Editor */}
              <div className="flex-1 p-6">
                <div className="mb-4 flex items-center space-x-2">
                  <button
                    onClick={() => formatText('bold')}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm font-bold"
                    title="Bold"
                  >
                    B
                  </button>
                  <button
                    onClick={() => formatText('italic')}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm italic"
                    title="Italic"
                  >
                    I
                  </button>
                  <button
                    onClick={() => formatText('underline')}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm underline"
                    title="Underline"
                  >
                    U
                  </button>
                  <button
                    onClick={() => formatText('section')}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
                    title="Section"
                  >
                    H1
                  </button>
                  <button
                    onClick={() => formatText('subsection')}
                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
                    title="Subsection"
                  >
                    H2
                  </button>
                </div>
                
                <textarea
                  ref={textareaRef}
                  value={latexContent}
                  onChange={(e) => setLatexContent(e.target.value)}
                  onSelect={handleTextSelection}
                  className="w-full h-96 p-4 border border-gray-300 rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Edit your LaTeX content here..."
                />
                
                <div className="mt-4 text-sm text-gray-500">
                  Selected text: {selectedText ? `"${selectedText.substring(0, 50)}${selectedText.length > 50 ? '...' : ''}"` : 'None'}
                </div>
              </div>

              {/* Side Panel */}
              <div className="w-80 border-l p-6">
                <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                
                <div className="space-y-3">
                  <button
                    onClick={() => enhanceTextWithAI('improve')}
                    disabled={!selectedText || processingAI}
                    className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {processingAI ? 'Processing...' : 'Improve Text'}
                  </button>
                  
                  <button
                    onClick={() => enhanceTextWithAI('formal')}
                    disabled={!selectedText || processingAI}
                    className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
                  >
                    Make Formal
                  </button>
                  
                  <button
                    onClick={() => enhanceTextWithAI('summary')}
                    disabled={!selectedText || processingAI}
                    className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
                  >
                    Summarize
                  </button>
                  
                  <button
                    onClick={() => enhanceTextWithAI('expand')}
                    disabled={!selectedText || processingAI}
                    className="w-full bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 disabled:opacity-50"
                  >
                    Expand Detail
                  </button>

                  <div className="border-t pt-3">
                    <h4 className="text-md font-medium mb-2">Translate</h4>
                    <button
                      onClick={() => translateText('English')}
                      disabled={!selectedText || processingAI}
                      className="w-full mb-2 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      To English
                    </button>
                    <button
                      onClick={() => translateText('Malay')}
                      disabled={!selectedText || processingAI}
                      className="w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      To Malay
                    </button>
                  </div>
                </div>

                {enhancementResult && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">AI Enhancement Result</h4>
                    <div className="text-sm">
                      <p className="mb-2"><strong>Type:</strong> {enhancementResult.enhancement_type}</p>
                      <p className="mb-2"><strong>AI Powered:</strong> {enhancementResult.ai_powered ? 'Yes' : 'No'}</p>
                      {enhancementResult.enhanced_text && (
                        <div className="mb-3">
                          <p className="font-medium">Enhanced Text:</p>
                          <p className="bg-white p-2 rounded border text-xs">
                            {enhancementResult.enhanced_text}
                          </p>
                          <button
                            onClick={() => applyEnhancement(enhancementResult.enhanced_text!)}
                            className="mt-2 bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700"
                          >
                            Apply Enhancement
                          </button>
                        </div>
                      )}
                      {enhancementResult.message && (
                        <p className="text-gray-600 text-xs">{enhancementResult.message}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'ai-tools' && (
            <div className="p-6">
              <div className="max-w-4xl mx-auto">
                <h3 className="text-2xl font-semibold mb-6">AI Writing Assistant</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Get AI Suggestions */}
                  <div className="bg-blue-50 p-6 rounded-lg">
                    <h4 className="text-lg font-semibold mb-4 text-blue-800">Content Analysis</h4>
                    <p className="text-gray-700 mb-4">
                      Get AI-powered suggestions to improve your report's writing quality, structure, and clarity.
                    </p>
                    <button
                      onClick={getAISuggestions}
                      disabled={loadingSuggestions}
                      className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {loadingSuggestions ? 'Analyzing...' : 'Analyze Content'}
                    </button>
                  </div>

                  {/* Text Enhancement */}
                  <div className="bg-green-50 p-6 rounded-lg">
                    <h4 className="text-lg font-semibold mb-4 text-green-800">Text Enhancement</h4>
                    <p className="text-gray-700 mb-4">
                      Select text in the editor and use AI to improve, formalize, summarize, or expand it.
                    </p>
                    <div className="text-sm text-gray-600">
                      Selected: {selectedText ? `"${selectedText.substring(0, 30)}..."` : 'No text selected'}
                    </div>
                  </div>
                </div>

                {/* AI Suggestions Display */}
                {aiSuggestions.length > 0 && (
                  <div className="mt-8">
                    <h4 className="text-xl font-semibold mb-4">AI Suggestions</h4>
                    <div className="space-y-4">
                      {aiSuggestions.map((suggestion, index) => (
                        <div key={index} className={`p-4 rounded-lg border-l-4 ${
                          suggestion.importance === 'high' ? 'bg-red-50 border-red-400' :
                          suggestion.importance === 'medium' ? 'bg-yellow-50 border-yellow-400' :
                          'bg-gray-50 border-gray-400'
                        }`}>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center mb-2">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  suggestion.category === 'grammar' ? 'bg-red-100 text-red-800' :
                                  suggestion.category === 'style' ? 'bg-blue-100 text-blue-800' :
                                  suggestion.category === 'clarity' ? 'bg-green-100 text-green-800' :
                                  suggestion.category === 'structure' ? 'bg-purple-100 text-purple-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {suggestion.category}
                                </span>
                                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                                  suggestion.importance === 'high' ? 'bg-red-100 text-red-800' :
                                  suggestion.importance === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {suggestion.importance}
                                </span>
                              </div>
                              <p className="text-gray-800">{suggestion.suggestion}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="p-6">
              <div className="bg-gray-100 p-6 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">LaTeX Content Preview</h3>
                <pre className="whitespace-pre-wrap font-mono text-sm bg-white p-4 rounded border overflow-auto max-h-96">
                  {latexContent}
                </pre>
                <div className="mt-4 text-sm text-gray-600">
                  <p>Lines: {latexContent.split('\n').length}</p>
                  <p>Characters: {latexContent.length}</p>
                  <p>Words: {latexContent.split(/\s+/).filter(word => word.length > 0).length}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedReportEditor;