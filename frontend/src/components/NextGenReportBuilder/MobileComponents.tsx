/**
 * Mobile-Optimized Components for Next-Gen Report Builder
 * Focus: Touch interactions, Responsive design, Progressive Enhancement
 * Following Luke Wroblewski's Mobile First principles
 */

import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Drawer,
  SwipeableDrawer,
  Fab,
  BottomNavigation,
  BottomNavigationAction,
  Card,
  CardContent,
  Grid,
  Chip,
  useTheme,
  useMediaQuery,
  Button,
  Tooltip,
  Zoom,
  Slide,
  alpha,
} from "@mui/material";
import {
  Add,
  DataObject,
  BarChart,
  Tune,
  Visibility,
  TouchApp,
  PanTool,
  SwipeUp,
  SwipeDown,
  SwipeLeft,
  SwipeRight,
  ExpandLess,
  ExpandMore,
  DragHandle,
  Close,
  CheckCircle,
} from "@mui/icons-material";

// Touch Gesture Hooks
const useTouchGestures = () => {
  const [gestureState, setGestureState] = useState({
    isDragging: false,
    isPinching: false,
    isLongPress: false,
    startPosition: { x: 0, y: 0 },
    currentPosition: { x: 0, y: 0 },
  });

  const longPressTimer = useRef<NodeJS.Timeout>();
  const touchStartTime = useRef<number>(0);

  const handleTouchStart = useCallback((event: React.TouchEvent) => {
    const touch = event.touches[0];
    touchStartTime.current = Date.now();
    
    setGestureState(prev => ({
      ...prev,
      startPosition: { x: touch.clientX, y: touch.clientY },
      currentPosition: { x: touch.clientX, y: touch.clientY },
    }));

    // Start long press detection
    longPressTimer.current = setTimeout(() => {
      setGestureState(prev => ({ ...prev, isLongPress: true }));
    }, 500);
  }, []);

  const handleTouchMove = useCallback((event: React.TouchEvent) => {
    const touch = event.touches[0];
    
    setGestureState(prev => {
      const deltaX = touch.clientX - prev.startPosition.x;
      const deltaY = touch.clientY - prev.startPosition.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      
      return {
        ...prev,
        currentPosition: { x: touch.clientX, y: touch.clientY },
        isDragging: distance > 10,
      };
    });

    // Clear long press if moved too much
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
    
    setGestureState({
      isDragging: false,
      isPinching: false,
      isLongPress: false,
      startPosition: { x: 0, y: 0 },
      currentPosition: { x: 0, y: 0 },
    });
  }, []);

  return {
    gestureState,
    touchHandlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
    },
  };
};

// Mobile Data Field Component
const MobileDataField: React.FC<{
  field: any;
  onSelect: (field: any) => void;
  isSelected: boolean;
}> = ({ field, onSelect, isSelected }) => {
  const theme = useTheme();
  const { gestureState, touchHandlers } = useTouchGestures();

  return (
    <Card
      variant="outlined"
      sx={{
        mb: 1,
        borderColor: isSelected ? "primary.main" : "grey.300",
        backgroundColor: isSelected 
          ? alpha(theme.palette.primary.main, 0.1)
          : "background.paper",
        transform: gestureState.isLongPress ? "scale(1.02)" : "scale(1)",
        transition: "all 0.2s ease",
        minHeight: 60,
        cursor: "pointer",
        touchAction: "manipulation", // Prevents double-tap zoom
      }}
      onClick={() => onSelect(field)}
      {...touchHandlers}
    >
      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
        <Box display="flex" alignItems="center" gap={1}>
          <DragHandle sx={{ color: "text.secondary" }} />
          {field.icon}
          <Box flex={1} minWidth={0}>
            <Typography variant="body2" fontWeight="medium" noWrap>
              {field.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {field.type} • {field.usageCount} uses
            </Typography>
          </Box>
          {isSelected && (
            <CheckCircle color="primary" sx={{ fontSize: 20 }} />
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// Mobile Bottom Panel with Swipe Gestures
const MobileBottomPanel: React.FC<{
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title: string;
}> = ({ open, onClose, children, title }) => {
  const theme = useTheme();
  const [dragOffset, setDragOffset] = useState(0);
  const panelRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = useCallback((event: React.TouchEvent) => {
    const touch = event.touches[0];
    panelRef.current?.setAttribute("data-start-y", touch.clientY.toString());
  }, []);

  const handleTouchMove = useCallback((event: React.TouchEvent) => {
    const startY = parseFloat(panelRef.current?.getAttribute("data-start-y") || "0");
    const currentY = event.touches[0].clientY;
    const offset = Math.max(0, currentY - startY);
    setDragOffset(offset);
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (dragOffset > 100) {
      onClose();
    }
    setDragOffset(0);
  }, [dragOffset, onClose]);

  return (
    <SwipeableDrawer
      anchor="bottom"
      open={open}
      onClose={onClose}
      onOpen={() => {}}
      disableSwipeToOpen
      PaperProps={{
        sx: {
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          maxHeight: "80vh",
          transform: `translateY(${dragOffset}px)`,
          transition: dragOffset === 0 ? "transform 0.3s ease" : "none",
        },
      }}
    >
      <Box
        ref={panelRef}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        sx={{ touchAction: "none" }}
      >
        {/* Drag Handle */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            pt: 1,
            pb: 1,
            cursor: "grab",
          }}
        >
          <Box
            sx={{
              width: 40,
              height: 4,
              backgroundColor: "grey.300",
              borderRadius: 2,
            }}
          />
        </Box>
        
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            px: 2,
            pb: 1,
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Typography variant="h6" fontWeight="semibold">
            {title}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
        
        {/* Content */}
        <Box sx={{ p: 2, maxHeight: "60vh", overflow: "auto" }}>
          {children}
        </Box>
      </Box>
    </SwipeableDrawer>
  );
};

// Mobile Chart Type Selector with Large Touch Targets
const MobileChartTypeSelector: React.FC<{
  chartTypes: any[];
  selectedType: string;
  onTypeSelect: (type: any) => void;
}> = ({ chartTypes, selectedType, onTypeSelect }) => {
  return (
    <Grid container spacing={2}>
      {chartTypes.map((chartType) => (
        <Grid item xs={6} key={chartType.id}>
          <Card
            variant="outlined"
            sx={{
              cursor: "pointer",
              minHeight: 120,
              border: selectedType === chartType.id ? 2 : 1,
              borderColor: selectedType === chartType.id ? "primary.main" : "grey.300",
              backgroundColor: selectedType === chartType.id 
                ? alpha("#6366f1", 0.1) 
                : "background.paper",
              transition: "all 0.2s ease",
              touchAction: "manipulation",
              "&:active": {
                transform: "scale(0.98)",
              },
            }}
            onClick={() => onTypeSelect(chartType)}
          >
            <CardContent 
              sx={{ 
                display: "flex", 
                flexDirection: "column", 
                alignItems: "center", 
                textAlign: "center",
                p: 2,
                "&:last-child": { pb: 2 },
              }}
            >
              <Box sx={{ fontSize: 32, mb: 1, color: "primary.main" }}>
                {chartType.icon}
              </Box>
              <Typography variant="body2" fontWeight="medium" mb={0.5}>
                {chartType.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {chartType.description}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

// Mobile Drop Zone with Haptic Feedback
const MobileDropZone: React.FC<{
  label: string;
  accepts: string[];
  currentField?: any;
  onDrop: (field: any) => void;
  onRemove: () => void;
}> = ({ label, accepts, currentField, onDrop, onRemove }) => {
  const theme = useTheme();
  const [isHighlighted, setIsHighlighted] = useState(false);

  // Simulate haptic feedback
  const triggerHapticFeedback = () => {
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        minHeight: 80,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        borderStyle: currentField ? "solid" : "dashed",
        borderWidth: 2,
        borderColor: currentField ? "primary.main" : "grey.300",
        backgroundColor: currentField 
          ? alpha(theme.palette.primary.main, 0.05)
          : isHighlighted 
            ? alpha(theme.palette.success.main, 0.1) 
            : "transparent",
        borderRadius: 2,
        transition: "all 0.2s ease",
        touchAction: "manipulation",
      }}
      onTouchStart={() => {
        setIsHighlighted(true);
        triggerHapticFeedback();
      }}
      onTouchEnd={() => setIsHighlighted(false)}
    >
      {currentField ? (
        <Box display="flex" alignItems="center" gap={1} width="100%">
          <Box flex={1} textAlign="center">
            <Typography variant="body2" fontWeight="medium">
              {currentField.name}
            </Typography>
            <Chip 
              label={currentField.type} 
              size="small" 
              sx={{ mt: 0.5, fontSize: "0.7rem" }} 
            />
          </Box>
          <IconButton size="small" onClick={onRemove}>
            <Close fontSize="small" />
          </IconButton>
        </Box>
      ) : (
        <Box textAlign="center">
          <TouchApp sx={{ fontSize: 32, color: "text.secondary", mb: 1 }} />
          <Typography variant="body2" fontWeight="medium">
            {label}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Tap to select {accepts.join(" or ")}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

// Mobile Navigation Tabs
const MobileNavigationTabs: React.FC<{
  activeTab: number;
  onTabChange: (tab: number) => void;
}> = ({ activeTab, onTabChange }) => {
  return (
    <BottomNavigation
      value={activeTab}
      onChange={(_, newValue) => onTabChange(newValue)}
      sx={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        borderTop: 1,
        borderColor: "divider",
        backgroundColor: "background.paper",
        "& .MuiBottomNavigationAction-root": {
          minWidth: "auto",
          px: 1,
        },
      }}
    >
      <BottomNavigationAction
        label="Data"
        icon={<DataObject />}
        sx={{ "&.Mui-selected": { color: "primary.main" } }}
      />
      <BottomNavigationAction
        label="Charts"
        icon={<BarChart />}
        sx={{ "&.Mui-selected": { color: "primary.main" } }}
      />
      <BottomNavigationAction
        label="Style"
        icon={<Tune />}
        sx={{ "&.Mui-selected": { color: "primary.main" } }}
      />
      <BottomNavigationAction
        label="Preview"
        icon={<Visibility />}
        sx={{ "&.Mui-selected": { color: "primary.main" } }}
      />
    </BottomNavigation>
  );
};

// Mobile Floating Action Menu
const MobileFloatingActionMenu: React.FC<{
  onAddChart: () => void;
  onAddText: () => void;
  onAddTable: () => void;
}> = ({ onAddChart, onAddText, onAddTable }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const theme = useTheme();

  const menuItems = [
    { label: "Chart", icon: <BarChart />, action: onAddChart },
    { label: "Text", icon: <Typography component="span">T</Typography>, action: onAddText },
    { label: "Table", icon: <DataObject />, action: onAddTable },
  ];

  return (
    <>
      {/* Menu Items */}
      {menuItems.map((item, index) => (
        <Zoom
          key={item.label}
          in={menuOpen}
          timeout={200 + index * 100}
          style={{ transitionDelay: menuOpen ? `${index * 50}ms` : "0ms" }}
        >
          <Fab
            size="small"
            color="primary"
            sx={{
              position: "fixed",
              bottom: 80 + (index + 1) * 60,
              right: 16,
              zIndex: 999,
            }}
            onClick={() => {
              item.action();
              setMenuOpen(false);
            }}
          >
            {item.icon}
          </Fab>
        </Zoom>
      ))}

      {/* Main FAB */}
      <Fab
        color="primary"
        sx={{
          position: "fixed",
          bottom: 80,
          right: 16,
          zIndex: 1000,
          transform: menuOpen ? "rotate(45deg)" : "rotate(0deg)",
          transition: "transform 0.2s ease",
        }}
        onClick={() => setMenuOpen(!menuOpen)}
      >
        <Add />
      </Fab>
    </>
  );
};

// Mobile-Optimized Report Canvas
const MobileReportCanvas: React.FC<{
  elements: any[];
  onElementSelect: (id: string) => void;
  selectedElementId: string | null;
}> = ({ elements, onElementSelect, selectedElementId }) => {
  return (
    <Box
      sx={{
        p: 2,
        pb: 10, // Account for bottom navigation
        minHeight: "100vh",
        touchAction: "pan-y", // Allow vertical scrolling
      }}
    >
      {elements.length === 0 ? (
        <Paper
          variant="outlined"
          sx={{
            p: 4,
            textAlign: "center",
            borderStyle: "dashed",
            borderColor: "grey.300",
            backgroundColor: alpha("#f3f4f6", 0.5),
          }}
        >
          <TouchApp sx={{ fontSize: 48, color: "text.secondary", mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Start Building Your Report
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Tap the + button to add charts, text, or tables
          </Typography>
          <Button variant="contained" startIcon={<Add />}>
            Add Your First Element
          </Button>
        </Paper>
      ) : (
        <Box display="flex" flexDirection="column" gap={2}>
          {elements.map((element) => (
            <Card
              key={element.id}
              variant={selectedElementId === element.id ? "outlined" : "elevation"}
              sx={{
                borderColor: selectedElementId === element.id ? "primary.main" : "transparent",
                borderWidth: 2,
                cursor: "pointer",
                touchAction: "manipulation",
                "&:active": {
                  transform: "scale(0.98)",
                },
              }}
              onClick={() => onElementSelect(element.id)}
            >
              <CardContent>
                <Typography variant="h6">{element.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {element.type}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
};

// Export all mobile components
export {
  useTouchGestures,
  MobileDataField,
  MobileBottomPanel,
  MobileChartTypeSelector,
  MobileDropZone,
  MobileNavigationTabs,
  MobileFloatingActionMenu,
  MobileReportCanvas,
};

export default MobileNavigationTabs;
