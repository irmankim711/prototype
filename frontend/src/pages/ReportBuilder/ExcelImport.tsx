import React from "react";
import { useRef } from "react";
import { Box, Button, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Alert } from "@mui/material";
import * as XLSX from 'xlsx';

interface ExcelImportProps {
  onDataParsed: (data: { headers: string[]; rows: any[] }) => void;
}

export default function ExcelImport({ onDataParsed }: ExcelImportProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = React.useState<{ headers: string[]; rows: any[] } | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    console.log('Excel file selected:', file.name, 'Size:', file.size);
    setError(null);
    
    const reader = new FileReader();
    reader.onload = (evt: any) => {
      try {
        console.log('File read successfully, processing...');
        const data = new Uint8Array(evt.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        
        console.log('Workbook sheets:', workbook.SheetNames);
        
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        console.log('Parsed JSON data:', json);
        console.log('Number of rows:', json.length);
        
        if (json.length === 0) {
          setError('Excel file appears to be empty');
          return;
        }
        
        const headers = json[0] as string[];
        const rows = json.slice(1);
        
        console.log('Headers:', headers);
        console.log('First few rows:', rows.slice(0, 3));
        
        if (headers.length === 0) {
          setError('No headers found in Excel file');
          return;
        }
        
        // Filter out completely empty rows
        const filteredRows = rows.filter((row: any) => 
          Array.isArray(row) && row.some((cell: any) => cell !== null && cell !== undefined && cell !== '')
        );
        
        console.log('Filtered rows:', filteredRows.length);
        
        setPreview({ headers, rows: filteredRows });
        onDataParsed({ headers, rows: filteredRows });
        
      } catch (error) {
        console.error('Error processing Excel file:', error);
        setError('Error processing Excel file. Please check the file format.');
      }
    };
    
    reader.onerror = () => {
      console.error('Error reading file');
      setError('Error reading file');
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
      
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      
      {preview && (
        <Box mt={2}>
          <Typography variant="subtitle1">Preview (first 10 rows):</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {preview.headers.map((header: any) => (
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
          <Alert severity="success" sx={{ mt: 2 }}>
            Successfully imported {preview.rows.length} rows with {preview.headers.length} columns
          </Alert>
        </Box>
      )}
    </Box>
  );
} 