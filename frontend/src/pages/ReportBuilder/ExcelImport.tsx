import React, { useRef } from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import * as XLSX from 'xlsx';

interface ExcelImportProps {
  onDataParsed: (data: { headers: string[]; rows: any[] }) => void;
}

export default function ExcelImport({ onDataParsed }: ExcelImportProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = React.useState<{ headers: string[]; rows: any[] } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      const headers = json[0] as string[];
      const rows = json.slice(1);
      setPreview({ headers, rows });
      onDataParsed({ headers, rows });
    };
    reader.readAsArrayBuffer(file);
  };

  return (
    <Box>
      <Button variant="contained" onClick={() => inputRef.current?.click()}>
        Upload Excel File
      </Button>
      <input
        type="file"
        accept=".xlsx,.xls"
        ref={inputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      {preview && (
        <Box mt={2}>
          <Typography variant="subtitle1">Preview (first 10 rows):</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {preview.headers.map((header) => (
                    <TableCell key={header}>{header}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {preview.rows.slice(0, 10).map((row, idx) => (
                  <TableRow key={idx}>
                    {preview.headers.map((_, colIdx) => (
                      <TableCell key={colIdx}>{row[colIdx]}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Box>
  );
} 