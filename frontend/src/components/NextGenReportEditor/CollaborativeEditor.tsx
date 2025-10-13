import React from 'react';
/**
 * Collaborative Editor Component
 * Real-time multi-user editing with conflict resolution and live cursors
 */

import { forwardRef, useEffect, useRef, useState, useCallback } from "react";
  
import { Box, Paper, TextField, Typography, Avatar, Chip, Tooltip, Fade, Badge } from "@mui/material";

import { styled } from "@mui/material/styles";

import { io, Socket } from "socket.io-client";

import type { EditorContent } from './ReportEditor';

import type { CollaborationSession, CollaborationUser } from '../../services/collaborationService';

interface CollaborativeEditorProps {
  content: EditorContent;
  
onChange: (content: Partial<EditorContent>) => void;
  
readOnly?: boolean;
  
collaborationSession?: CollaborationSession | null;
  
reportId: number;
}

interface CursorPosition {
  userId: string;
  
userName: string;
  
userColor: string;
  
position: {
    line: number,
    
column: number,
  };
  
selection?: {
    start: { line: number, 
column: number };
    
end: { line: number, 
column: number };
  };
}

interface EditOperation {
  type: 'insert' | 'delete' | 'replace';
  
position: { line: number, 
column: number };
  
content?: string;
  
length?: number;
  
userId: string;
  
timestamp: number;
}

export const EditorContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.paper,
}));

export const EditorContent = styled(Box)(({ theme }) => ({
  flex: 1,
  padding: theme.spacing(3),
  overflow: 'auto',
  position: 'relative',
  '& .editor-content': {
    minHeight: '100%',
    outline: 'none',
    lineHeight: 1.6,
    fontSize: '16px',
    fontFamily: theme.typography.body1.fontFamily,
    '&:focus': {
      outline: 'none',
    },
  },
}));

export const CursorIndicator = styled(Box)<{ color: string }>(({ color }) => ({
  position: 'absolute',
  width: '2px',
  height: '20px',
  backgroundColor: color,
  zIndex: 1000,
  pointerEvents: 'none',
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '-4px',
    left: '-4px',
    width: '10px',
    height: '4px',
    backgroundColor: color,
    borderRadius: '2px',
  },
}));

export const SelectionHighlight = styled(Box)<{ color: string }>(({ color }) => ({
  position: 'absolute',
  backgroundColor: `${color}33`,
  border: `1px solid ${color}66`,
  pointerEvents: 'none',
  zIndex: 999,
}));

export const UserPresenceIndicator = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(1),
  right: theme.spacing(1),
  display: 'flex',
  gap: theme.spacing(0.5),
  zIndex: 1001,
}));

export const CollaborativeEditor = forwardRef<HTMLDivElement, CollaborativeEditorProps>(
  ({ content, onChange, readOnly = false, collaborationSession, reportId }, ref) => {
    const [socket, setSocket] = useState<Socket | null>(null);
    
const [activeCursors, setActiveCursors] = useState<Map<string, CursorPosition>>(new Map());
    
const [activeUsers, setActiveUsers] = useState<CollaborationUser[]>([]);
    
const [isConnected, setIsConnected] = useState(false);
    
const [operationQueue, setOperationQueue] = useState<EditOperation[]>([]);

const editorRef = useRef<HTMLDivElement>(null);
    
const currentUserRef = useRef<CollaborationUser | null>(null);
    
const lastContentRef = useRef<string>(content.content);

    // User colors for collaboration
    const userColors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ];

    // Initialize WebSocket connection
    useEffect(() => {
      if (!collaborationSession || readOnly) return;

const socketInstance = io(`${import.meta.env.VITE_API_URL || 'http://localhost:5001'}/editor`, {
        auth: {
          token: localStorage.getItem('access_token') || localStorage.getItem('accessToken'),
        },
      });

socketInstance.on('connect', () => {
        setIsConnected(true);
        
socketInstance.emit('join-room', {
          reportId,
          sessionId: collaborationSession.id,
        });
      });

socketInstance.on('disconnect', () => {
        setIsConnected(false);
      });

socketInstance.on('user-joined', (user: CollaborationUser) => {
        setActiveUsers(prev => [...prev.filter(u => u.id !== user.id), user]);
      });

socketInstance.on('user-left', (userId: string) => {
        setActiveUsers(prev => prev.filter(u => u.id !== userId));
        
setActiveCursors(prev => {
          const newCursors = new Map(prev);
          
newCursors.delete(userId);
          
return newCursors;
        });
      });

socketInstance.on('cursor-update', (cursorData: CursorPosition) => {
        setActiveCursors(prev => {
          const newCursors = new Map(prev);
          
newCursors.set(cursorData.userId, cursorData);
          
return newCursors;
        });
      });

socketInstance.on('operation', (operation: EditOperation) => {
        applyRemoteOperation(operation);
      });

socketInstance.on('content-sync', (syncedContent: string) => {
        if (syncedContent !== lastContentRef.current) {
          onChange({ content: syncedContent });
          
lastContentRef.current = syncedContent;
        }
      });

setSocket(socketInstance);

return () => {
        socketInstance.disconnect();
      };
    }, [collaborationSession, readOnly, reportId]);

    // Apply remote operations
    const applyRemoteOperation = useCallback((operation: EditOperation) => {
      if (!editorRef.current) return;

const editor = editorRef.current;
      
const selection = window.getSelection();
      
      // Store current selection
      const currentRange = selection?.rangeCount ? selection.getRangeAt(0) : null;

try {
        switch (operation.type) {
          case 'insert':
            if (operation.content) {
              // Apply insert operation
              const textNode = document.createTextNode(operation.content);
              // Insert at specified position
              // This is a simplified implementation
              editor.appendChild(textNode);
            }
            break;
          
case 'delete':
            // Apply delete operation
            // This is a simplified implementation
            break;
          
case 'replace':
            // Apply replace operation
            // This is a simplified implementation
            break;
        }
        
        // Restore selection if it was preserved
        if (currentRange && selection) {
          selection.removeAllRanges();
          
selection.addRange(currentRange);
        }
        
        // Update content
        onChange({ content: editor.innerHTML });
        
lastContentRef.current = editor.innerHTML;
        
      } catch (error) {
        console.error('Failed to apply remote operation:', error);
      }
    }, [onChange]);

    // Handle local content changes
    const handleContentChange = useCallback((event: React.FormEvent<HTMLDivElement>) => {
      if (readOnly) return;

const newContent = event.currentTarget.innerHTML;
      
const oldContent = lastContentRef.current;

if (newContent !== oldContent) {
        // Generate operation for the change
        const operation: EditOperation = {
          type: 'replace', // Simplified - in real implementation, would detect specific changes
          position: { line: 0, column: 0 },
          content: newContent,
          userId: currentUserRef.current?.id || 'anonymous',
          timestamp: Date.now(),
        };

        // Send operation to other users
        if (socket && isConnected) {
          socket.emit('operation', operation);
        }

        // Update local state
        onChange({ content: newContent });
        
lastContentRef.current = newContent;
      }
    }, [readOnly, socket, isConnected, onChange]);

    // Handle cursor position changes
    const handleSelectionChange = useCallback(() => {
      if (readOnly || !socket || !isConnected || !currentUserRef.current) return;

const selection = window.getSelection();
      
if (!selection || selection.rangeCount === 0) return;

const range = selection.getRangeAt(0);
      
const rect = range.getBoundingClientRect();

if (rect.width === 0 && rect.height === 0) return;

const cursorPosition: CursorPosition = {
        userId: currentUserRef.current.id,
        userName: currentUserRef.current.name,
        userColor: userColors[activeUsers.findIndex(u => u.id === currentUserRef.current?.id) % userColors.length],
        position: {
          line: 0, // Simplified - would calculate actual line/column
          column: 0,
        },
      };

if (!selection.isCollapsed) {
        cursorPosition.selection = {
          start: { line: 0, column: 0 },
          end: { line: 0, column: 0 },
        };
      }

      socket.emit('cursor-update', cursorPosition);
    }, [readOnly, socket, isConnected, activeUsers]);

    // Set up selection change listener
    useEffect(() => {
      document.addEventListener('selectionchange', handleSelectionChange);
      
return () => document.removeEventListener('selectionchange', handleSelectionChange);
    }, [handleSelectionChange]);

    // Handle title changes
    const handleTitleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
      if (readOnly) return;
      
onChange({ title: event.target.value });
    }, [readOnly, onChange]);

    // Get user color
    const getUserColor = (userId: string): string => {
      const userIndex = activeUsers.findIndex(u => u.id === userId);
      
return userColors[userIndex % userColors.length];
    };

return (
      <EditorContainer>
        {/* User Presence Indicators */}
        <UserPresenceIndicator>
          <Fade in={isConnected}>
            <Chip
              size="small"
              label={`${activeUsers.length} online`}
              color={isConnected ? 'success' : 'default'}
              variant="outlined"
            />
          </Fade>
          
          {activeUsers.slice(0, 5).map((user: any) => (
            <Tooltip key={user.id} title={user.name}>
              <Badge
                color="success"
                variant="dot"
                invisible={!isConnected}
              >
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    fontSize: '0.875rem',
                    bgcolor: getUserColor(user.id),
                  }}
                >
                  {user.name.charAt(0).toUpperCase()}
                </Avatar>
              </Badge>
            </Tooltip>
          ))}
          
          {activeUsers.length > 5 && (
            <Tooltip title={`+${activeUsers.length - 5} more users`}>
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  fontSize: '0.75rem',
                  bgcolor: 'grey.400',
                }}
              >
                +{activeUsers.length - 5}
              </Avatar>
            </Tooltip>
          )}
        </UserPresenceIndicator>

        {/* Title Editor */}
        <Box sx={{ p: 3, pb: 0 }}>
          <TextField
            fullWidth
            variant="standard"
            placeholder="Report Title"
            value={content.title}
            onChange={handleTitleChange}
            disabled={readOnly}
            InputProps={{
              style: {
                fontSize: '2rem',
                fontWeight: 'bold',
              },
              disableUnderline: readOnly,
            }}
          />
        </Box>

        {/* Main Editor */}
        <EditorContent>
          <Box
            ref={editorRef}
            className="editor-content"
            contentEditable={!readOnly}
            suppressContentEditableWarning
            onInput={handleContentChange}
            dangerouslySetInnerHTML={{ __html: content.content }}
            sx={{
              position: 'relative',
              minHeight: '400px',
              padding: 2,
              border: readOnly ? 'none' : '1px solid transparent',
              borderRadius: 1,
              '&:focus': {
                borderColor: 'primary.main',
                outline: 'none',
              },
              '& p': { margin: '8px 0' },
              '& h1, & h2, & h3, & h4, & h5, & h6': { margin: '16px 0 8px 0' },
              '& ul, & ol': { margin: '8px 0', paddingLeft: '24px' },
              '& blockquote': {
                borderLeft: '4px solid #e0e0e0',
                margin: '16px 0',
                paddingLeft: '16px',
                fontStyle: 'italic',
                color: 'text.secondary',
              },
              '& table': {
                borderCollapse: 'collapse',
                width: '100%',
                margin: '16px 0',
              },
              '& td, & th': {
                border: '1px solid #e0e0e0',
                padding: '8px',
                textAlign: 'left',
              },
              '& th': {
                backgroundColor: 'grey.100',
                fontWeight: 'bold',
              },
              '& code': {
                backgroundColor: 'grey.100',
                padding: '2px 4px',
                borderRadius: '4px',
                fontFamily: 'monospace',
              },
              '& pre': {
                backgroundColor: 'grey.100',
                padding: '16px',
                borderRadius: '4px',
                overflow: 'auto',
                fontFamily: 'monospace',
              },
            }}
          />

          {/* Render active cursors */}
          {Array.from(activeCursors.values()).map((cursor: any) => (
            <React.Fragment key={cursor.userId}>
              <CursorIndicator
                color={cursor.userColor}
                sx={{
                  // Position would be calculated based on cursor.position
                  top: 100, // Placeholder
                  left: 100, // Placeholder
                }}
              />
              
              {cursor.selection && (
                <SelectionHighlight
                  color={cursor.userColor}
                  sx={{
                    // Position and size would be calculated based on selection
                    top: 100, // Placeholder
                    left: 100, // Placeholder
                    width: 100, // Placeholder
                    height: 20, // Placeholder
                  }}
                />
              )}
              
              <Tooltip title={cursor.userName}>
                <Chip
                  size="small"
                  label={cursor.userName}
                  sx={{
                    position: 'absolute',
                    top: 80, // Placeholder - would be calculated
                    left: 100, // Placeholder - would be calculated
                    backgroundColor: cursor.userColor,
                    color: 'white',
                    fontSize: '0.75rem',
                    height: '20px',
                    zIndex: 1002,
                  }}
                />
              </Tooltip>
            </React.Fragment>
          ))}
        </EditorContent>

        {/* Document Statistics */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
          <Typography variant="caption" color="text.secondary">
            Words: {content.metadata.wordCount} | Characters: {content.metadata.characterCount} | 
            Last modified: {content.metadata.lastModified.toLocaleTimeString()}
            {isConnected && (
              <> | <span style={{ color: '#4caf50' }}>● Connected</span></>
            )}
          </Typography>
        </Box>
      </EditorContainer>
    );
  }
);

CollaborativeEditor.displayName = 'CollaborativeEditor';

export default CollaborativeEditor;
