import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  IconButton,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  styled,
  CssBaseline,
  Button,
  Avatar,
  Menu,
  Divider,
  Tooltip,
  Badge,
  Collapse,
} from "@mui/material";
import { MenuItem as MuiMenuItem } from "@mui/material";
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Assignment as SubmissionIcon,
  Create as FormIcon,
  BarChart as GenerateReportIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  ChevronLeft as ChevronLeftIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DescriptionIcon,
  InsertDriveFile as FileIcon,
  Notifications as NotificationsIcon,
  Help as HelpIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
} from "@mui/icons-material";

const drawerWidth = 240;

// Styled components to match StratoSys design
const SidebarHeader = styled(Box)(() => ({
  padding: "20px 16px",
  backgroundColor: "#0e1c40",
  color: "white",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  height: "80px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.12)",
}));

const StyledDrawer = styled(Drawer)(() => ({
  "& .MuiDrawer-paper": {
    width: drawerWidth,
    boxSizing: "border-box",
    backgroundColor: "#0e1c40",
    color: "rgba(255, 255, 255, 0.9)",
    boxShadow: "2px 0 10px rgba(0,0,0,0.1)",
    border: "none",
    "&::-webkit-scrollbar": {
      width: "6px",
    },
    "&::-webkit-scrollbar-track": {
      background: "transparent",
    },
    "&::-webkit-scrollbar-thumb": {
      backgroundColor: "rgba(255, 255, 255, 0.2)",
      borderRadius: "3px",
    },
  },
}));

const StyledAppBar = styled(AppBar)(() => ({
  backgroundColor: "#ffffff",
  color: "#333333",
  boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
  zIndex: 1201,
  borderBottom: "1px solid rgba(0, 0, 0, 0.05)",
  padding: "0 24px",
}));

const MenuItem = styled(ListItemButton, {
  shouldForwardProp: (prop) => prop !== "selected",
})((props) => ({
  margin: "4px 12px",
  borderRadius: "8px",
  color: props.selected ? "white" : "rgba(255, 255, 255, 0.7)",
  backgroundColor: props.selected ? "rgba(255, 255, 255, 0.1)" : "transparent",
  "&:hover": {
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    color: "white",
    "& .MuiListItemIcon-root": {
      color: "white",
    },
  },
  transition: "all 0.2s ease",
  padding: "10px 16px",
  "& .MuiListItemIcon-root": {
    color: props.selected ? "white" : "rgba(255, 255, 255, 0.6)",
    minWidth: "40px",
    transition: "color 0.2s ease",
  },
}));

const MenuText = styled(ListItemText)({
  "& .MuiTypography-root": {
    fontSize: "0.95rem",
    fontWeight: 500,
    fontFamily: '"Poppins", sans-serif',
  },
});

interface LayoutProps {
  children: React.ReactNode;
}

// Interface for menu items with nested submenu support
interface MenuItem {
  text: string;
  icon: React.ReactNode;
  path?: string;
  onClick?: (e: React.MouseEvent, navigate: (path: string) => void) => void;
  submenu?: MenuItem[];
  badge?: number;
}

const menuItems: MenuItem[] = [
  {
    text: "Admin Dashboard",
    icon: <DashboardIcon />,
    path: "/dashboard",
  },
  {
    text: "Reports",
    icon: <DescriptionIcon />,
    submenu: [
      {
        text: "Generate Report",
        icon: <GenerateReportIcon />,
        path: "/reports/new",
      },
      {
        text: "Report Templates",
        icon: <FileIcon />,
        path: "/reports/templates",
      },
      {
        text: "Previous Reports",
        icon: <DescriptionIcon />,
        path: "/reports/previous",
      },
    ],
  },
  {
    text: "Submissions",
    icon: <SubmissionIcon />,
    path: "/submission",
    badge: 3,
  },
  { text: "Form Builder", icon: <FormIcon />, path: "/form" },
  { text: "User Profile", icon: <PersonIcon />, path: "/profile" },
  { text: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [expandedSubmenu, setExpandedSubmenu] = useState<string | null>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] =
    useState<null | HTMLElement>(null);
  const [helpAnchorEl, setHelpAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const open = Boolean(anchorEl);
  const notificationsOpen = Boolean(notificationAnchorEl);
  const helpOpen = Boolean(helpAnchorEl);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotificationMenu = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleHelpMenu = (event: React.MouseEvent<HTMLElement>) => {
    setHelpAnchorEl(event.currentTarget);
  };

  // Toggle submenu expansion
  const handleSubmenuToggle = (text: string) => {
    setExpandedSubmenu(expandedSubmenu === text ? null : text);
  };

  // This function is used to handle menu item clicks
  const handleItemClick = (e: React.MouseEvent, item: MenuItem) => {
    if (item.submenu) {
      handleSubmenuToggle(item.text);
    } else if (item.onClick) {
      item.onClick(e, navigate);
    } else if (item.path) {
      navigate(item.path);
    }
    setMobileOpen(false);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationsClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleHelpClose = () => {
    setHelpAnchorEl(null);
  };

  const handleLogout = () => {
    // Clear authentication token and user data
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    // Navigate back to landing page
    navigate("/");
  };

  const handleProfileClick = () => {
    navigate("/profile");
    handleClose();
  };

  useEffect(() => {
    // Add Poppins font to the document
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap";
    document.head.appendChild(link);

    // Add Font Awesome for icons
    const fontAwesome = document.createElement("link");
    fontAwesome.rel = "stylesheet";
    fontAwesome.href =
      "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css";
    document.head.appendChild(fontAwesome);

    return () => {
      document.head.removeChild(link);
      document.head.removeChild(fontAwesome);
    };
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <SidebarHeader>
        <Box sx={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Box
            sx={{
              width: "36px",
              height: "36px",
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <DashboardIcon sx={{ color: "white", fontSize: "20px" }} />
          </Box>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              fontFamily: '"Poppins", sans-serif',
              fontWeight: 600,
              fontSize: "1.1rem",
              lineHeight: "1.2",
              color: "white",
            }}
          >
            StratoSys
            <br />
            Report
          </Typography>
        </Box>
        <IconButton
          onClick={() => setMobileOpen(false)}
          sx={{
            color: "rgba(255, 255, 255, 0.7)",
            display: { sm: "none" },
            "&:hover": {
              backgroundColor: "rgba(255, 255, 255, 0.1)",
            },
          }}
        >
          <ChevronLeftIcon />
        </IconButton>
      </SidebarHeader>
      <Box sx={{ flexGrow: 1, overflowY: "auto", padding: "8px 0" }}>
        <List sx={{ padding: 0 }}>
          {menuItems.map((item) => (
            <Box key={item.text}>
              <MenuItem
                selected={
                  item.submenu
                    ? item.submenu.some(
                        (subItem) => location.pathname === subItem.path
                      ) || expandedSubmenu === item.text
                    : location.pathname === item.path
                }
                onClick={(e) => handleItemClick(e, item)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <MenuText primary={item.text} />
                {item.badge && (
                  <Badge
                    badgeContent={item.badge}
                    color="error"
                    sx={{ ml: 1 }}
                  />
                )}
                {item.submenu &&
                  (expandedSubmenu === item.text ? (
                    <ExpandLessIcon />
                  ) : (
                    <ExpandMoreIcon />
                  ))}
              </MenuItem>

              {item.submenu && (
                <Collapse
                  in={expandedSubmenu === item.text}
                  timeout="auto"
                  unmountOnExit
                >
                  <List component="div" disablePadding>
                    {item.submenu.map((subItem) => (
                      <MenuItem
                        key={subItem.text}
                        selected={location.pathname === subItem.path}
                        onClick={(e) => handleItemClick(e, subItem)}
                        sx={{ pl: 4, backgroundColor: "transparent" }}
                      >
                        <ListItemIcon>{subItem.icon}</ListItemIcon>
                        <MenuText primary={subItem.text} />
                        <KeyboardArrowRightIcon
                          sx={{
                            fontSize: "1rem",
                            opacity: 0.5,
                            ml: "auto",
                            color: "rgba(255, 255, 255, 0.4)",
                          }}
                        />
                      </MenuItem>
                    ))}
                  </List>
                </Collapse>
              )}
            </Box>
          ))}
        </List>
      </Box>
      <Box
        sx={{
          padding: "16px",
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <Button
          fullWidth
          variant="outlined"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{
            color: "rgba(255, 255, 255, 0.7)",
            borderColor: "rgba(255, 255, 255, 0.2)",
            textTransform: "none",
            borderRadius: "8px",
            padding: "8px 16px",
            "&:hover": {
              backgroundColor: "rgba(255, 99, 71, 0.1)",
              borderColor: "rgba(255, 99, 71, 0.5)",
              color: "#ff6347",
            },
          }}
        >
          Logout
        </Button>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <StyledAppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: "none" } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ fontFamily: '"Poppins", sans-serif', fontWeight: 500 }}
          >
            {menuItems.find((item) => item.path === location.pathname)?.text ||
              "StratoSys Report"}
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Tooltip title="Help & Resources">
              <IconButton
                size="medium"
                onClick={handleHelpMenu}
                aria-controls="help-menu"
                aria-haspopup="true"
                sx={{
                  backgroundColor: "rgba(0, 0, 0, 0.03)",
                  "&:hover": {
                    backgroundColor: "rgba(0, 0, 0, 0.05)",
                  },
                }}
              >
                <HelpIcon sx={{ fontSize: "20px", color: "#5f6368" }} />
              </IconButton>
            </Tooltip>

            <Tooltip title="Notifications">
              <IconButton
                size="medium"
                onClick={handleNotificationMenu}
                aria-controls="notification-menu"
                aria-haspopup="true"
                sx={{
                  backgroundColor: "rgba(0, 0, 0, 0.03)",
                  "&:hover": {
                    backgroundColor: "rgba(0, 0, 0, 0.05)",
                  },
                }}
              >
                <Badge badgeContent={3} color="error">
                  <NotificationsIcon
                    sx={{ fontSize: "20px", color: "#5f6368" }}
                  />
                </Badge>
              </IconButton>
            </Tooltip>

            <Tooltip title="Account">
              <IconButton
                size="medium"
                onClick={handleMenu}
                aria-controls="menu-appbar"
                aria-haspopup="true"
                sx={{
                  backgroundColor: "rgba(0, 0, 0, 0.03)",
                  "&:hover": {
                    backgroundColor: "rgba(0, 0, 0, 0.05)",
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: "32px",
                    height: "32px",
                    backgroundColor: "#0e1c40",
                    color: "white",
                    fontSize: "14px",
                    fontWeight: 500,
                  }}
                >
                  JD
                </Avatar>
              </IconButton>
            </Tooltip>

            {/* Help Menu */}
            <Menu
              id="help-menu"
              anchorEl={helpAnchorEl}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
              }}
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
              open={helpOpen}
              onClose={handleHelpClose}
              PaperProps={{
                elevation: 0,
                sx: {
                  overflow: "visible",
                  filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.1))",
                  mt: 1.5,
                  width: 250,
                  "&:before": {
                    content: '""',
                    display: "block",
                    position: "absolute",
                    top: 0,
                    right: 14,
                    width: 10,
                    height: 10,
                    bgcolor: "background.paper",
                    transform: "translateY(-50%) rotate(45deg)",
                    zIndex: 0,
                  },
                },
              }}
            >
              <Typography sx={{ p: 2, fontWeight: 500, color: "#0e1c40" }}>
                Help Resources
              </Typography>
              <Divider />
              <MuiMenuItem onClick={handleHelpClose}>
                <ListItemIcon>
                  <DescriptionIcon fontSize="small" />
                </ListItemIcon>
                Documentation
              </MuiMenuItem>
              <MuiMenuItem onClick={handleHelpClose}>
                <ListItemIcon>
                  <HelpIcon fontSize="small" />
                </ListItemIcon>
                FAQ
              </MuiMenuItem>
              <MuiMenuItem onClick={handleHelpClose}>
                <ListItemIcon>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                Support
              </MuiMenuItem>
            </Menu>

            {/* Notifications Menu */}
            <Menu
              id="notification-menu"
              anchorEl={notificationAnchorEl}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
              }}
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
              open={notificationsOpen}
              onClose={handleNotificationsClose}
              PaperProps={{
                elevation: 0,
                sx: {
                  overflow: "visible",
                  filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.1))",
                  mt: 1.5,
                  width: 320,
                  maxHeight: 400,
                  overflowY: "auto",
                  "&:before": {
                    content: '""',
                    display: "block",
                    position: "absolute",
                    top: 0,
                    right: 14,
                    width: 10,
                    height: 10,
                    bgcolor: "background.paper",
                    transform: "translateY(-50%) rotate(45deg)",
                    zIndex: 0,
                  },
                },
              }}
            >
              <Box
                sx={{
                  p: 2,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography sx={{ fontWeight: 500, color: "#0e1c40" }}>
                  Notifications
                </Typography>
                <Button
                  size="small"
                  sx={{ color: "#4a69dd", textTransform: "none" }}
                >
                  Mark all as read
                </Button>
              </Box>
              <Divider />
              {[
                {
                  title: "New report submitted",
                  time: "2 hours ago",
                  read: false,
                },
                {
                  title: "System update completed",
                  time: "Yesterday",
                  read: true,
                },
                {
                  title: "Your report has been approved",
                  time: "3 days ago",
                  read: true,
                },
              ].map((notification, index) => (
                <Box key={index}>
                  <MuiMenuItem
                    onClick={handleNotificationsClose}
                    sx={{ py: 2 }}
                  >
                    <Box
                      sx={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        bgcolor: notification.read ? "transparent" : "#4a69dd",
                        mr: 1.5,
                        mt: 0.5,
                      }}
                    />
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: notification.read ? 400 : 600,
                          color: notification.read ? "#64748b" : "#0e1c40",
                        }}
                      >
                        {notification.title}
                      </Typography>
                      <Typography variant="caption" sx={{ color: "#94a3b8" }}>
                        {notification.time}
                      </Typography>
                    </Box>
                  </MuiMenuItem>
                  {index < 2 && <Divider />}
                </Box>
              ))}
              <Box sx={{ p: 1, textAlign: "center" }}>
                <Button
                  fullWidth
                  size="small"
                  sx={{
                    color: "#4a69dd",
                    textTransform: "none",
                    "&:hover": {
                      backgroundColor: "rgba(74, 105, 221, 0.05)",
                    },
                  }}
                >
                  View all notifications
                </Button>
              </Box>
            </Menu>

            {/* User Profile Menu */}
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
              }}
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
              open={open}
              onClose={handleClose}
              PaperProps={{
                elevation: 0,
                sx: {
                  overflow: "visible",
                  filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.1))",
                  mt: 1.5,
                  "& .MuiAvatar-root": {
                    width: 32,
                    height: 32,
                    ml: -0.5,
                    mr: 1,
                  },
                  "&:before": {
                    content: '""',
                    display: "block",
                    position: "absolute",
                    top: 0,
                    right: 14,
                    width: 10,
                    height: 10,
                    bgcolor: "background.paper",
                    transform: "translateY(-50%) rotate(45deg)",
                    zIndex: 0,
                  },
                },
              }}
            >
              <Box sx={{ px: 2, py: 1.5 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  John Doe
                </Typography>
                <Typography variant="body2" sx={{ color: "#64748b" }}>
                  john.doe@example.com
                </Typography>
              </Box>
              <Divider />
              <MuiMenuItem onClick={handleProfileClick}>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                Profile
              </MuiMenuItem>
              <MuiMenuItem onClick={handleClose}>
                <ListItemIcon>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                Settings
              </MuiMenuItem>
              <Divider />
              <MuiMenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                Logout
              </MuiMenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </StyledAppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <StyledDrawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: "block", sm: "none" },
          }}
        >
          {drawer}
        </StyledDrawer>
        <StyledDrawer
          variant="permanent"
          sx={{
            display: { xs: "none", sm: "block" },
          }}
          open
        >
          {drawer}
        </StyledDrawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          marginLeft: { sm: `${drawerWidth}px` },
          marginTop: "64px",
          transition: "all 0.2s ease",
        }}
      >
        <Box sx={{ maxWidth: "1200px", margin: "0 auto" }}>{children}</Box>
      </Box>
    </Box>
  );
}
