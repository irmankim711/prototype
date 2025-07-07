import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  styled,
  Chip,
  Pagination,
  FormControl,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';

// Styled components
const PageTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: '1.5rem',
  color: '#333',
  marginBottom: '1rem',
  borderBottom: '2px solid #1e3a8a',
  paddingBottom: '0.5rem',
  display: 'inline-block',
}));

const StyledTableContainer = styled(TableContainer)(() => ({
  borderRadius: '4px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  marginTop: '1.5rem',
  border: '1px solid #eaeaea',
}));

const StyledTableHead = styled(TableHead)(() => ({
  backgroundColor: '#f8f9fa',
}));

const StyledTableCell = styled(TableCell)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 500,
  fontSize: '0.9rem',
  padding: '12px 16px',
  borderBottom: '1px solid #eaeaea',
}));

const StyledTableRow = styled(TableRow)(() => ({
  '&:hover': {
    backgroundColor: '#f5f7fa',
  },
}));

const ScoreChip = styled(Chip)<{ score: number }>(({ score }) => {
  let backgroundColor = '#4caf50';
  let color = 'white';
  
  if (score < 80) {
    backgroundColor = '#ff9800';
  }
  if (score < 70) {
    backgroundColor = '#f44336';
  }
  
  return {
    fontWeight: 600,
    fontSize: '0.85rem',
    backgroundColor,
    color,
    height: '28px',
    width: '28px',
    borderRadius: '50%',
    '.MuiChip-label': {
      padding: '0px',
    },
  };
});

const ViewButton = styled(Button)(() => ({
  backgroundColor: '#3f51b5',
  borderRadius: '4px',
  textTransform: 'none',
  fontWeight: 500,
  fontSize: '0.9rem',
  '&:hover': {
    backgroundColor: '#303f9f',
  },
}));

const ExportButton = styled(Button)(() => ({
  backgroundColor: '#3f51b5',
  borderRadius: '4px',
  textTransform: 'none',
  fontWeight: 500,
  '&:hover': {
    backgroundColor: '#303f9f',
  },
}));

interface Submission {
  id: string;
  name: string;
  email: string;
  date: string;
  score: number;
}

export default function SubmissionPage() {
  const [filter, setFilter] = useState<string>('All Submissions');
  
  // Mock data for submissions
  const submissions: Submission[] = [
    { id: '1', name: 'Alice Johnson', email: 'alice@email.com', date: '2025-05-10', score: 94 },
    { id: '2', name: 'Bob Smith', email: 'bob@email.com', date: '2025-05-09', score: 85 },
    { id: '3', name: 'Charlie Brown', email: 'charlie@email.com', date: '2025-05-08', score: 78 },
    { id: '4', name: 'Diana Ross', email: 'diana@email.com', date: '2025-05-11', score: 92 },
    { id: '5', name: 'Eve Williams', email: 'eve@email.com', date: '2025-05-07', score: 88 },
  ];

  const handleFilterChange = (event: SelectChangeEvent<string>) => {
    setFilter(event.target.value as string);
  };

  const handleExport = () => {
    // In a real app, this would export data
    console.log('Exporting data');
  };

  return (
    <Box>
      <PageTitle>
        Submission
      </PageTitle>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <Select
            value={filter}
            onChange={handleFilterChange as any}
            displayEmpty
            sx={{
              fontFamily: '"Poppins", sans-serif',
              fontSize: '0.9rem',
              '.MuiOutlinedInput-notchedOutline': {
                borderColor: '#ccc',
              },
            }}
          >
            <MenuItem value="All Submissions">All Submissions</MenuItem>
            <MenuItem value="Recent">Recent</MenuItem>
            <MenuItem value="High Score">High Score</MenuItem>
            <MenuItem value="Low Score">Low Score</MenuItem>
          </Select>
        </FormControl>

        <ExportButton
          variant="contained"
          startIcon={<i className="fas fa-file-export"></i>}
          onClick={handleExport}
        >
          Export
        </ExportButton>
      </Box>

      <StyledTableContainer>
        <Box sx={{ p: 2, borderBottom: '1px solid #eaeaea' }}>
          <Typography variant="h6" sx={{ fontWeight: 500 }}>
            Recent Submissions
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Showing 1-5 of 25
          </Typography>
        </Box>
        <Table>
          <StyledTableHead>
            <TableRow>
              <StyledTableCell>Name</StyledTableCell>
              <StyledTableCell>Email</StyledTableCell>
              <StyledTableCell>Date</StyledTableCell>
              <StyledTableCell>Score</StyledTableCell>
              <StyledTableCell>Action</StyledTableCell>
            </TableRow>
          </StyledTableHead>
          <TableBody>
            {submissions.map((submission) => (
              <StyledTableRow key={submission.id}>
                <StyledTableCell>{submission.name}</StyledTableCell>
                <StyledTableCell>{submission.email}</StyledTableCell>
                <StyledTableCell>
                  {new Date(submission.date).toLocaleDateString()}
                </StyledTableCell>
                <StyledTableCell>
                  <ScoreChip 
                    label={submission.score} 
                    score={submission.score} 
                    size="small" 
                  />
                </StyledTableCell>
                <StyledTableCell>
                  <ViewButton
                    variant="contained"
                    size="small"
                  >
                    View
                  </ViewButton>
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <Pagination count={5} shape="rounded" size="small" />
        </Box>
      </StyledTableContainer>
    </Box>
  );
}
