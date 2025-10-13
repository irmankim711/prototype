import React from 'react';
/**
 * Editing Toolbar Component
 * Provides formatting and content modification tools for the report editor
 */

import { useState } from "react";
  
import { Box, Toolbar, IconButton, Divider, Tooltip, ButtonGroup, Menu, MenuItem, ListItemIcon, ListItemText, Typography, ToggleButton, ToggleButtonGroup } from "@mui/material";
  
import { FormatBold, FormatItalic, FormatUnderlined, FormatStrikethrough, FormatListBulleted, FormatListNumbered, FormatQuote, FormatAlignLeft, FormatAlignCenter, FormatAlignRight, FormatAlignJustify, Title, Image, TableChart, Link, Code, FormatColorText, FormatColorFill, Undo, Redo, ExpandMore, InsertChart, AttachFile, VideoLibrary } from "@mui/icons-material";

interface EditingToolbarProps {
  onFormatText: (format: string, value?: string) => void;
  
onInsertElement: (elementType: string) => void;
  
disabled?: boolean;
}

const EditingToolbar: React.FC<EditingToolbarProps> = ({
  onFormatText,
  onInsertElement,
  disabled = false,
}) => {
  const [headingMenuAnchor, setHeadingMenuAnchor] = useState<null | HTMLElement>(null);
  
const [insertMenuAnchor, setInsertMenuAnchor] = useState<null | HTMLElement>(null);
  
const [colorMenuAnchor, setColorMenuAnchor] = useState<null | HTMLElement>(null);
  
const [alignment, setAlignment] = useState<string>('left');

const handleHeadingMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setHeadingMenuAnchor(event.currentTarget);
  };

const handleInsertMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setInsertMenuAnchor(event.currentTarget);
  };

const handleColorMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setColorMenuAnchor(event.currentTarget);
  };

const handleHeadingSelect = (level: number) => {
    onFormatText('formatBlock', `h${level}`);
    
setHeadingMenuAnchor(null);
  };

const handleAlignmentChange = (
    event: React.MouseEvent<HTMLElement>,
    newAlignment: string | null,
  ) => {
    if (newAlignment !== null) {
      setAlignment(newAlignment);
      
onFormatText(`justify${newAlignment.charAt(0).toUpperCase() + newAlignment.slice(1)}`);
    }
  };

const handleColorSelect = (color: string) => {
    onFormatText('foreColor', color);
    
setColorMenuAnchor(null);
  };

const textColors = [
    '#000000', '#333333', '#666666', '#999999', '#CCCCCC',
    '#FF0000', '#FF6600', '#FFCC00', '#00FF00', '#0066FF',
    '#6600FF', '#FF00FF', '#00FFFF', '#FFFF00', '#FF9999',
  ];

return (
    <Box sx={{ borderTop: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Toolbar variant="dense" sx={{ minHeight: 48, gap: 1 }}>
        {/* Undo/Redo */}
        <ButtonGroup size="small" disabled={disabled}>
          <Tooltip title="Undo (Ctrl+Z)">
            <IconButton onClick={() => onFormatText('undo')}>
              <Undo />
            </IconButton>
          </Tooltip>
          <Tooltip title="Redo (Ctrl+Shift+Z)">
            <IconButton onClick={() => onFormatText('redo')}>
              <Redo />
            </IconButton>
          </Tooltip>
        </ButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Text Formatting */}
        <ButtonGroup size="small" disabled={disabled}>
          <Tooltip title="Bold (Ctrl+B)">
            <IconButton onClick={() => onFormatText('bold')}>
              <FormatBold />
            </IconButton>
          </Tooltip>
          <Tooltip title="Italic (Ctrl+I)">
            <IconButton onClick={() => onFormatText('italic')}>
              <FormatItalic />
            </IconButton>
          </Tooltip>
          <Tooltip title="Underline (Ctrl+U)">
            <IconButton onClick={() => onFormatText('underline')}>
              <FormatUnderlined />
            </IconButton>
          </Tooltip>
          <Tooltip title="Strikethrough">
            <IconButton onClick={() => onFormatText('strikeThrough')}>
              <FormatStrikethrough />
            </IconButton>
          </Tooltip>
        </ButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Headings */}
        <Tooltip title="Headings">
          <IconButton
            onClick={handleHeadingMenuOpen}
            disabled={disabled}
            size="small"
          >
            <Title />
            <ExpandMore fontSize="small" />
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={headingMenuAnchor}
          open={Boolean(headingMenuAnchor)}
          onClose={() => setHeadingMenuAnchor(null)}
        >
          <MenuItem onClick={() => handleHeadingSelect(1)}>
            <Typography variant="h4">Heading 1</Typography>
          </MenuItem>
          <MenuItem onClick={() => handleHeadingSelect(2)}>
            <Typography variant="h5">Heading 2</Typography>
          </MenuItem>
          <MenuItem onClick={() => handleHeadingSelect(3)}>
            <Typography variant="h6">Heading 3</Typography>
          </MenuItem>
          <MenuItem onClick={() => onFormatText('formatBlock', 'p')}>
            <Typography variant="body1">Normal Text</Typography>
          </MenuItem>
        </Menu>

        <Divider orientation="vertical" flexItem />

        {/* Lists */}
        <ButtonGroup size="small" disabled={disabled}>
          <Tooltip title="Bullet List">
            <IconButton onClick={() => onFormatText('insertUnorderedList')}>
              <FormatListBulleted />
            </IconButton>
          </Tooltip>
          <Tooltip title="Numbered List">
            <IconButton onClick={() => onFormatText('insertOrderedList')}>
              <FormatListNumbered />
            </IconButton>
          </Tooltip>
          <Tooltip title="Quote">
            <IconButton onClick={() => onInsertElement('quote')}>
              <FormatQuote />
            </IconButton>
          </Tooltip>
        </ButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Alignment */}
        <ToggleButtonGroup
          value={alignment}
          exclusive
          onChange={handleAlignmentChange}
          size="small"
          disabled={disabled}
        >
          <ToggleButton value="left" aria-label="align left">
            <Tooltip title="Align Left">
              <FormatAlignLeft />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="center" aria-label="align center">
            <Tooltip title="Align Center">
              <FormatAlignCenter />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="right" aria-label="align right">
            <Tooltip title="Align Right">
              <FormatAlignRight />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="justify" aria-label="justify">
            <Tooltip title="Justify">
              <FormatAlignJustify />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Colors */}
        <Tooltip title="Text Color">
          <IconButton
            onClick={handleColorMenuOpen}
            disabled={disabled}
            size="small"
          >
            <FormatColorText />
            <ExpandMore fontSize="small" />
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={colorMenuAnchor}
          open={Boolean(colorMenuAnchor)}
          onClose={() => setColorMenuAnchor(null)}
        >
          <Box sx={{ p: 1, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 0.5 }}>
            {textColors.map((color: any) => (
              <Box
                key={color}
                onClick={() => handleColorSelect(color)}
                sx={{
                  width: 24,
                  height: 24,
                  backgroundColor: color,
                  border: 1,
                  borderColor: 'divider',
                  cursor: 'pointer',
                  borderRadius: 0.5,
                  '&:hover': {
                    transform: 'scale(1.1)',
                  },
                }}
              />
            ))}
          </Box>
        </Menu>

        <Divider orientation="vertical" flexItem />

        {/* Insert Elements */}
        <Tooltip title="Insert">
          <IconButton
            onClick={handleInsertMenuOpen}
            disabled={disabled}
            size="small"
          >
            <AttachFile />
            <ExpandMore fontSize="small" />
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={insertMenuAnchor}
          open={Boolean(insertMenuAnchor)}
          onClose={() => setInsertMenuAnchor(null)}
        >
          <MenuItem onClick={() => { onInsertElement('image'); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <Image />
            </ListItemIcon>
            <ListItemText>Image</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onInsertElement('table'); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <TableChart />
            </ListItemIcon>
            <ListItemText>Table</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onInsertElement('chart'); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <InsertChart />
            </ListItemIcon>
            <ListItemText>Chart</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onInsertElement('video'); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <VideoLibrary />
            </ListItemIcon>
            <ListItemText>Video</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onFormatText('createLink', prompt('Enter URL:') || ''); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <Link />
            </ListItemIcon>
            <ListItemText>Link</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onInsertElement('code'); 
setInsertMenuAnchor(null); }}>
            <ListItemIcon>
              <Code />
            </ListItemIcon>
            <ListItemText>Code Block</ListItemText>
          </MenuItem>
        </Menu>

        <Box sx={{ flexGrow: 1 }} />

        {/* Additional Tools */}
        <ButtonGroup size="small" disabled={disabled}>
          <Tooltip title="Remove Formatting">
            <IconButton onClick={() => onFormatText('removeFormat')}>
              <FormatColorFill />
            </IconButton>
          </Tooltip>
        </ButtonGroup>
      </Toolbar>
    </Box>
  );
};

export default EditingToolbar;
