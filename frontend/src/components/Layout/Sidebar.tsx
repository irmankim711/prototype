import React, { useState, useContext } from "react";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Toolbar,
  Divider,
  Box,
  Avatar,
  Typography,
  Button,
} from "@mui/material";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";

import ListAltIcon from "@mui/icons-material/ListAlt";
import TableChartIcon from "@mui/icons-material/TableChart";
import HistoryIcon from "@mui/icons-material/History";
import DescriptionIcon from "@mui/icons-material/Description";
import SettingsIcon from "@mui/icons-material/Settings";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import BuildIcon from "@mui/icons-material/Build";
import HomeIcon from "@mui/icons-material/Home";
import { AuthContext } from "../../context/AuthContext";

const drawerWidth = 240;

const navItems = [
  { label: "Home", icon: <HomeIcon />, path: "/" },
  { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },

  { label: "Submissions", icon: <ListAltIcon />, path: "/submission" },
  {
    label: "Reports",
    icon: <TableChartIcon />,
    children: [
      { label: "Report Builder", icon: <BuildIcon />, path: "/report-builder" },
      {
        label: "Report History",
        icon: <HistoryIcon />,
        path: "/report-history",
      },
      {
        label: "Templates",
        icon: <DescriptionIcon />,
        path: "/report-templates",
      },
      {
        label: "Real-time",
        icon: <TableChartIcon />,
        path: "/realtime-dashboard",
      },
    ],
  },
  { label: "Form Builder", icon: <BuildIcon />, path: "/form-builder-admin" },
  { label: "Profile", icon: <AccountCircleIcon />, path: "/profile" },
  { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

const sidebarBg = "linear-gradient(135deg, #16213a 0%, #233554 100%)";
const activeBg = "rgba(0, 153, 255, 0.18)";
const activeBar = "#33bfff";
const accentBlue = "#33bfff";

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [openReports, setOpenReports] = useState(true);
  const { user, logout } = useContext(AuthContext);

  // Use real user if available, else fallback
  const displayUser = {
    name:
      (user as { name?: string; email?: string; avatar?: string } | null)
        ?.name || "John Doe",
    email:
      (user as { name?: string; email?: string; avatar?: string } | null)
        ?.email || "john.doe@company.com",
    avatar:
      (user as { name?: string; email?: string; avatar?: string } | null)
        ?.avatar ||
      "https://ui-avatars.com/api/?name=John+Doe&background=0e1c40&color=fff",
  };

  const handleReportsClick = () => {
    setOpenReports((prev) => !prev);
  };

  const handleLogout = async () => {
    try {
      await logout();
      // Navigate back to landing page after successful logout
      navigate("/");
    } catch (error) {
      console.error("Logout failed:", error);
      // Even if logout fails, clear local state and navigate to landing page
      navigate("/");
    }
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: "border-box",
          background: sidebarBg,
          color: "#fff",
          borderRight: "none",
          boxShadow: "2px 0 12px 0 rgba(20,30,60,0.10)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        },
      }}
    >
      <Box>
        <Toolbar />
        <Box
          sx={{
            px: 2,
            py: 2,
            fontWeight: 700,
            fontSize: 22,
            color: "#fff",
            letterSpacing: 1,
            mb: 1,
          }}
        >
          <Box component="span" sx={{ color: accentBlue }}>
            StratoSys
          </Box>{" "}
          Report
        </Box>
        <Divider sx={{ borderColor: "rgba(255,255,255,0.10)", mb: 1 }} />
        <List>
          {navItems.map((item) => {
            if (item.children) {
              const isActive = item.children.some(
                (child) => location.pathname === child.path
              );
              return (
                <React.Fragment key={item.label}>
                  <ListItemButton
                    onClick={handleReportsClick}
                    selected={isActive}
                    sx={{
                      color: "#fff",
                      background: isActive ? activeBg : "none",
                      borderLeft: isActive
                        ? `4px solid ${activeBar}`
                        : "4px solid transparent",
                      "&:hover": { background: "rgba(0,0,0,0.10)" },
                    }}
                  >
                    <ListItemIcon sx={{ color: "#fff" }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.label} />
                    {openReports ? <ExpandLess /> : <ExpandMore />}
                  </ListItemButton>
                  <Collapse in={openReports} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {item.children.map((child) => {
                        const childActive = location.pathname === child.path;
                        return (
                          <ListItemButton
                            key={child.label}
                            component={NavLink}
                            to={child.path}
                            selected={childActive}
                            sx={{
                              pl: 4,
                              color: "#fff",
                              background: childActive ? activeBg : "none",
                              borderLeft: childActive
                                ? `4px solid ${activeBar}`
                                : "4px solid transparent",
                              "&:hover": { background: "rgba(0,0,0,0.13)" },
                            }}
                          >
                            <ListItemIcon sx={{ color: "#fff" }}>
                              {child.icon}
                            </ListItemIcon>
                            <ListItemText primary={child.label} />
                          </ListItemButton>
                        );
                      })}
                    </List>
                  </Collapse>
                </React.Fragment>
              );
            }
            const isActive = location.pathname === item.path;
            return (
              <ListItemButton
                key={item.label}
                component={NavLink}
                to={item.path}
                selected={isActive}
                sx={{
                  color: "#fff",
                  background: isActive ? activeBg : "none",
                  borderLeft: isActive
                    ? `4px solid ${activeBar}`
                    : "4px solid transparent",
                  "&:hover": { background: "rgba(0,0,0,0.10)" },
                }}
              >
                <ListItemIcon sx={{ color: "#fff" }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            );
          })}
        </List>
      </Box>
      {/* User profile section at the bottom */}
      <Box
        sx={{
          px: 2,
          py: 3,
          borderTop: "1px solid rgba(255,255,255,0.10)",
          background: "rgba(20,30,60,0.98)",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
          <Avatar
            src={displayUser.avatar}
            alt={displayUser.name}
            sx={{ width: 40, height: 40, mr: 1 }}
          />
          <Box>
            <Typography
              variant="body1"
              sx={{ color: "#fff", fontWeight: 600, fontSize: 16 }}
            >
              {displayUser.name}
            </Typography>
            <Typography variant="body2" sx={{ color: "#b0b8c1", fontSize: 13 }}>
              {displayUser.email}
            </Typography>
          </Box>
        </Box>
        <Button
          variant="outlined"
          color="primary"
          fullWidth
          onClick={handleLogout}
          sx={{
            mt: 1,
            borderColor: accentBlue,
            color: "#fff",
            background: "rgba(51,191,255,0.07)",
            fontWeight: 600,
            letterSpacing: 1,
            "&:hover": {
              background: accentBlue,
              color: "#fff",
              borderColor: accentBlue,
            },
          }}
        >
          Logout
        </Button>
      </Box>
    </Drawer>
  );
}
