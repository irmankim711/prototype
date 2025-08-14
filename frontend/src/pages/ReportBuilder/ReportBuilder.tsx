import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  MenuItem,
  Chip,
  Divider,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import {
  generateReportWithExcel,
  downloadReport,
  fetchTemplatePlaceholders,
} from '../../services/api';
import * as XLSX from 'xlsx';

// Dynamic Report Generator (Excel-first + JSON preview)
// - Excel upload -> backend mapping -> DOCX
// - Optional JSON editor + client-side preview (docxtemplater + mammoth)
// - Template placeholders + Excel headers + mapping summary

let Docxtemplater: any;
let PizZip: any;
let saveAs: any;
let mammothLib: any;

async function ensureDocxDeps() {
  if (!Docxtemplater) {
    const mod = await import('docxtemplater');
    Docxtemplater = mod.default || mod;
  }
  if (!PizZip) {
    const mod = await import('pizzip');
    PizZip = mod.default || mod;
  }
  if (!saveAs) {
    const mod = await import('file-saver');
    saveAs = mod.saveAs || mod.default;
  }
  if (!mammothLib) {
    const mod = await import('mammoth');
    mammothLib = mod.default || mod;
  }
}

function isJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

// Simple mapping summary: show which placeholders have likely matches in Excel headers
function MappingSummary({ placeholders, headers }: { placeholders: string[]; headers: string[] }) {
  const headerSet = new Set(headers.map((h) => h.toLowerCase()));
  const summary = placeholders.reduce(
    (acc: { matched: string[]; unmatched: string[] }, ph) => {
      // Match by trailing token (e.g., program.title -> title, signature.consultant.name -> name,
      // participants loop fields should be p.name -> name) – heuristic only
      const tail = ph.split('.').pop() || ph;
      if (headerSet.has(tail.toLowerCase())) acc.matched.push(ph);
      else acc.unmatched.push(ph);
      return acc;
    },
    { matched: [], unmatched: [] }
  );

  return (
    <Box sx={{ mt: 1 }}>
      <Typography variant="caption" sx={{ display: 'block', color: '#334155' }}>
        Likely matched: {summary.matched.slice(0, 10).join(', ')}{summary.matched.length > 10 ? '…' : ''}
      </Typography>
      {summary.unmatched.length > 0 && (
        <Typography variant="caption" color="error" sx={{ display: 'block' }}>
          Unmatched (check Excel headers or template): {summary.unmatched.slice(0, 10).join(', ')}{summary.unmatched.length > 10 ? '…' : ''}
        </Typography>
      )}
    </Box>
  );
}

const sampleContext = {
  program: {
    title: 'Sample Training Program',
    date: '01/02/2025',
    time: '9:00 AM - 5:00 PM',
    location: 'Main Hall',
    organizer: 'ABC Org',
    place: 'Campus A',
    total_participants: '2',
  },
  participants: [
    { bil: '1', name: 'Ali', ic: '900101-01-1234', address: 'Address 1', tel: '0123456789', pre_mark: '50', post_mark: '80' },
    { bil: '2', name: 'Siti', ic: '920202-02-5678', address: 'Address 2', tel: '0198765432', pre_mark: '60', post_mark: '75' },
  ],
  signature: {
    consultant: { name: 'Consultant Name' },
    executive: { name: 'Executive Name' },
    head: { name: 'Head Name' },
  },
};

export default function ReportBuilder() {
  // Core state
  const [templateName, setTemplateName] = useState<string>('Temp1.docx');
  const [templates, setTemplates] = useState<string[]>(['Temp1.docx']);

  // Excel
  const [selectedExcelFile, setSelectedExcelFile] = useState<File | null>(null);
  const [excelHeaders, setExcelHeaders] = useState<string[]>([]);

  // Template placeholders
  const [templatePlaceholders, setTemplatePlaceholders] = useState<string[]>([]);

  // JSON preview state
  const [jsonData, setJsonData] = useState<string>(JSON.stringify(sampleContext, null, 2));
  const [previewHtml, setPreviewHtml] = useState<string>('');

  // UX state
  const [aiPrompt, setAiPrompt] = useState<string>('Generate sample training program data with 5 participants');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [ready, setReady] = useState<boolean>(false);

  // Init
  useEffect(() => {
    ensureDocxDeps().then(() => setReady(true)).catch(() => setReady(false));
  }, []);

  // Load templates list from backend if available
  useEffect(() => {
    fetch('/api/mvp/templates/list')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((list) => {
        const names = Array.isArray(list)
          ? list.map((x: any) => x.filename || x.name || x.id).filter(Boolean)
          : [];
        if (names.length) setTemplates(names);
      })
      .catch(() => {});
  }, []);

  // Fetch placeholders for selected template
  useEffect(() => {
    if (!templateName) {
      setTemplatePlaceholders([]);
      return;
    }
    fetchTemplatePlaceholders(templateName)
      .then(setTemplatePlaceholders)
      .catch(() => setTemplatePlaceholders([]));
  }, [templateName]);

  // Derived JSON object
  const parsedData = useMemo(() => {
    if (!jsonData) return {} as any;
    return isJson(jsonData) ? JSON.parse(jsonData) : ({} as any);
  }, [jsonData]);

  // Debounced preview render using mammoth
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!isJson(jsonData)) {
        setPreviewHtml('<p style="color:#ef4444">Invalid JSON</p>');
        return;
      }
      try {
        await ensureDocxDeps();
        const res = await fetch(`/temp/${encodeURIComponent(templateName)}`);
        if (!res.ok) {
          setPreviewHtml('<p style="color:#ef4444">Template not found</p>');
          return;
        }
        const arrayBuffer = await res.arrayBuffer();
        const zip = new PizZip(arrayBuffer);
        const doc = new Docxtemplater(zip, { paragraphLoop: true, linebreaks: true });
        doc.setData(parsedData);
        doc.render();
        const out = doc.getZip().generate({ type: 'arraybuffer' });
        const { value: html } = await mammothLib.convertToHtml({ arrayBuffer: out });
        setPreviewHtml(html || '<p>No content</p>');
      } catch (e) {
        setPreviewHtml('<p style="color:#ef4444">Error generating preview</p>');
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [jsonData, templateName]);

  // Export JSON -> DOCX in browser (client-side path)
  const handleExport = async () => {
    setError(null);
    if (!isJson(jsonData)) {
      setError('Invalid JSON in data. Please fix and try again.');
      return;
    }
    try {
      setLoading(true);
      await ensureDocxDeps();
      const res = await fetch(`/temp/${encodeURIComponent(templateName)}`);
      if (!res.ok) {
        throw new Error(`Template not found at /temp/${templateName}. Place the .docx in frontend/public/temp/`);
      }
      const arrayBuffer = await res.arrayBuffer();
      const zip = new PizZip(arrayBuffer);
      const doc = new Docxtemplater(zip, { paragraphLoop: true, linebreaks: true });
      doc.setData(parsedData);
      doc.render();
      const out = doc.getZip().generate({
        type: 'blob',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const filename = `report_${templateName.replace(/\.docx$/i, '')}_${Date.now()}.docx`;
      saveAs(out, filename);
    } catch (e: any) {
      setError(e?.message || 'DOCX generation failed');
    } finally {
      setLoading(false);
    }
  };

  // When Excel file is selected, parse headers for mapping guidance
  const handleExcelSelected = (file: File) => {
    setSelectedExcelFile(file);
    setExcelHeaders([]);
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt: any) => {
      try {
        const data = new Uint8Array(evt.target.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: 'array' });
        const sheetName = wb.SheetNames[0];
        const ws = wb.Sheets[sheetName];
        const rows: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: null });
        if (rows && rows.length > 0) {
          const headers = (rows[0] as any[]).map((h) => String(h || '').trim()).filter(Boolean);
          setExcelHeaders(headers);
        }
      } catch (err) {
        console.error('Excel parse error:', err);
      }
    };
    reader.readAsArrayBuffer(file);
  };

  return (
    <Box sx={{ p: 1 }}>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Dynamic Report Generator
      </Typography>
      <Typography variant="body2" sx={{ mb: 2, color: '#475569' }}>
        Excel-first workflow. Upload Excel, select a template, see placeholders and detected columns, then generate a DOCX. JSON preview/export remains available for advanced users.
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>Template & Data</Typography>
              <TextField
                select
                label="Select Template"
                fullWidth
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                sx={{ mb: 2 }}
              >
                {templates.map((t) => (
                  <MenuItem key={t} value={t}>{t}</MenuItem>
                ))}
              </TextField>

              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Excel-based Generation</Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                <input
                  id="excel-upload-input"
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    const f = e.target.files?.[0] || null;
                    if (f) handleExcelSelected(f);
                  }}
                />
                {selectedExcelFile && (
                  <Chip size="small" label={`Selected: ${selectedExcelFile.name}`} />
                )}
              </Box>
              {excelHeaders.length > 0 && (
                <Typography variant="caption" sx={{ display: 'block', color: '#334155', mb: 1 }}>
                  Detected Excel columns: {excelHeaders.join(', ')}
                </Typography>
              )}

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Template Placeholders</Typography>
              {templatePlaceholders.length === 0 ? (
                <Typography variant="caption" color="text.secondary">No placeholders detected or failed to load.</Typography>
              ) : (
                <>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    {templatePlaceholders.length} placeholders found. Example: {templatePlaceholders.slice(0, 8).join(', ')}{templatePlaceholders.length > 8 ? '…' : ''}
                  </Typography>
                  {excelHeaders.length > 0 && (
                    <MappingSummary placeholders={templatePlaceholders} headers={excelHeaders} />
                  )}
                </>
              )}

              <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={async () => {
                    if (!selectedExcelFile) {
                      setError('Please upload an Excel file (.xlsx or .xls)');
                      return;
                    }
                    setError(null);
                    setLoading(true);
                    try {
                      const result = await generateReportWithExcel(templateName, selectedExcelFile);
                      if (!result?.success) throw new Error(result?.message || 'Excel generation failed');
                      await downloadReport(result.downloadUrl);
                    } catch (e: any) {
                      setError(e?.message || 'Failed to generate from Excel');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={loading || !ready}
                >
                  {loading ? 'Processing Excel…' : 'Generate DOCX from Excel'}
                </Button>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Optional: JSON Preview/Export</Typography>
              <TextField
                label="AI Prompt"
                fullWidth
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                sx={{ mb: 1 }}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={async () => {
                  setLoading(true);
                  try {
                    const res = await fetch('/api/ai/generate-json', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ prompt: aiPrompt }),
                    });
                    if (!res.ok) throw new Error('AI generation failed');
                    const data = await res.json();
                    const generatedJson = JSON.stringify(data.json || data, null, 2);
                    setJsonData(generatedJson);
                  } catch (e: any) {
                    setError(e?.message || 'AI generation failed');
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                Generate Data with AI
              </Button>

              <Box sx={{ mt: 2 }}>
                <React.Suspense
                  fallback={
                    <TextField
                      fullWidth
                      multiline
                      minRows={18}
                      value={jsonData}
                      onChange={(e) => setJsonData(e.target.value)}
                    />
                  }
                >
                  {/* Monaco fallback note: if react-monaco-editor bundling is problematic in your env, switch to @monaco-editor/react */}
                  {/* @ts-ignore */}
                  {(() => {
                    const Monaco = React.lazy(() => import('react-monaco-editor'));
                    return (
                      // @ts-ignore
                      <Monaco
                        width="100%"
                        height="400"
                        language="json"
                        theme="vs-dark"
                        value={jsonData}
                        onChange={(val: string) => setJsonData(val)}
                        options={{ minimap: { enabled: false }, automaticLayout: true }}
                      />
                    );
                  })()}
                </React.Suspense>
              </Box>

              <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleExport}
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <DownloadIcon />}
                  disabled={loading || !ready}
                >
                  {loading ? 'Generating…' : 'Export DOCX (JSON)'}
                </Button>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>Live Preview</Typography>
              <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
            </CardContent>
          </Card>

          <Box sx={{ mt: 2, p: 2, border: '1px dashed #cbd5e1', borderRadius: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>Tips</Typography>
            <Typography variant="caption" sx={{ display: 'block', color: '#334155' }}>
              • Loops in tables must use Jinja2: {"{% for p in participants %} … {% endfor %}"}
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', color: '#334155' }}>
              • Keep labels outside braces: {"{{ p.pre_mark }}"} PRE (not {"{{ p.pre_mark PRE }}"}).
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', color: '#334155' }}>
              • Ensure Excel headers map to keys like program.title, participants[].name, signature.consultant.name.
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
