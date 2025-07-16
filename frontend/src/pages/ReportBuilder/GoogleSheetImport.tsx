import React from 'react';
import { Box, Button, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
// @ts-ignore
import GooglePicker from 'react-google-picker';

interface GoogleSheetImportProps {
  onDataParsed: (data: { headers: string[]; rows: any[] }) => void;
  apiKey: string;
  clientId: string;
}

export default function GoogleSheetImport({ onDataParsed, apiKey, clientId }: GoogleSheetImportProps) {
  const [preview, setPreview] = React.useState<{ headers: string[]; rows: any[] } | null>(null);
  const [sheetUrl, setSheetUrl] = React.useState<string | null>(null);

  // This function would fetch the sheet data using Google Sheets API
  // For demo, it just simulates a preview
  const fetchSheetData = async (url: string) => {
    // TODO: Implement real Google Sheets API fetch
    // Simulate headers and rows
    const headers = ['Name', 'Email', 'Score'];
    const rows = [
      ['Alice', 'alice@example.com', 95],
      ['Bob', 'bob@example.com', 88],
      ['Charlie', 'charlie@example.com', 92],
    ];
    setPreview({ headers, rows });
    onDataParsed({ headers, rows });
  };

  return (
    <Box>
      <GooglePicker
        clientId={clientId}
        developerKey={apiKey}
        scope={['https://www.googleapis.com/auth/drive.readonly']}
        onChange={(data: any) => {
          if (data && data.docs && data.docs[0]) {
            setSheetUrl(data.docs[0].url);
            fetchSheetData(data.docs[0].url);
          }
        }}
        multiselect={false}
        navHidden={true}
        authImmediate={false}
        viewId={'SPREADSHEETS'}
      >
        <Button variant="contained">Import from Google Sheets</Button>
      </GooglePicker>
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