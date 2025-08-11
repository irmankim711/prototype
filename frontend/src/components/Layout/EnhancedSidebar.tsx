import React from "react";
import { useState, useContext } from "react";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Box,
  Avatar,
  Typography,
  Button,
  Chip,
  alpha,
  styled,
  keyframes,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Dashboard as DashboardIcon,
  ListAlt as ListAltIcon,
  Build as BuildIcon,
  Settings as SettingsIcon,
  ExpandLess,
  Assessment as ReportsIcon,
  History as HistoryIcon,
  Description as TemplatesIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  AutoAwesome as AutomatedReportsIcon,
} from "@mui/icons-material";
import { AuthContext } from "../../context/AuthContext";
import { useUser } from "../../hooks/useUser";

const drawerWidth = 260;

// Enhanced animations
const slideIn = keyframes`
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
`;

// Enhanced styled components
const StyledDrawer = styled(Drawer)(() => ({
  width: drawerWidth,
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: drawerWidth,
    boxSizing: "border-box",
    background: `
      linear-gradient(135deg, 
        ${alpha("#1e293b", 0.98)} 0%, 
        ${alpha("#334155", 0.95)} 50%, 
        ${alpha("#475569", 0.92)} 100%
      )
    `,
    backdropFilter: "blur(20px)",
    color: "#fff",
    borderRight: `1px solid ${alpha("#6366f1", 0.2)}`,
    boxShadow: `
      4px 0 20px ${alpha("#000", 0.15)},
      0 0 40px ${alpha("#6366f1", 0.1)}
    `,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    position: "relative",
    overflow: "hidden",
    "&::before": {
      content: '""',
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      height: "4px",
      background:
        "linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)",
    },
  },
}));

const LogoBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3, 2, 2),
  textAlign: "center",
  position: "relative",
  background: `linear-gradient(135deg, ${alpha(
    "#6366f1",
    0.1
  )} 0%, transparent 100%)`,
  borderBottom: `1px solid ${alpha("#6366f1", 0.2)}`,
  marginBottom: theme.spacing(1),
  "&::after": {
    content: '""',
    position: "absolute",
    bottom: 0,
    left: "50%",
    transform: "translateX(-50%)",
    width: "60px",
    height: "2px",
    background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
    borderRadius: "2px",
  },
}));

const StyledListItemButton = styled(ListItemButton, {
  shouldForwardProp: (prop: string) => prop !== "isActive",
})<{ isActive?: boolean }>(({ theme, isActive }) => ({
  margin: theme.spacing(0.5, 1),
  borderRadius: "12px",
  padding: theme.spacing(1.5, 2),
  color: "#e2e8f0",
  position: "relative",
  overflow: "hidden",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  animation: `${slideIn} 0.6s ease-out`,

  background: isActive
    ? `linear-gradient(135deg, ${alpha("#6366f1", 0.2)} 0%, ${alpha(
        "#8b5cf6",
        0.15
      )} 100%)`
    : "transparent",

  border: isActive
    ? `1px solid ${alpha("#6366f1", 0.3)}`
    : "1px solid transparent",

  "&::before": {
    content: '""',
    position: "absolute",
    left: 0,
    top: 0,
    height: "100%",
    width: isActive ? "4px" : "0px",
    background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
    borderRadius: "0 4px 4px 0",
    transition: "width 0.3s ease",
  },

  "&::after": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background:
      "linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent)",
    transform: "translateX(-100%)",
    transition: "transform 0.6s ease",
  },

  "&:hover": {
    background: isActive
      ? `linear-gradient(135deg, ${alpha("#6366f1", 0.25)} 0%, ${alpha(
          "#8b5cf6",
          0.2
        )} 100%)`
      : `linear-gradient(135deg, ${alpha("#6366f1", 0.1)} 0%, ${alpha(
          "#8b5cf6",
          0.05
        )} 100%)`,

    border: `1px solid ${alpha("#6366f1", 0.4)}`,
    transform: "translateY(-2px)",
    boxShadow: `0 8px 25px ${alpha("#6366f1", 0.2)}`,

    "&::after": {
      transform: "translateX(100%)",
    },

    "& .MuiListItemIcon-root": {
      transform: "scale(1.1)",
      color: "#6366f1",
    },

    "& .MuiListItemText-primary": {
      color: "#ffffff",
      fontWeight: 600,
    },
  },

  "& .MuiListItemIcon-root": {
    color: isActive ? "#6366f1" : "#94a3b8",
    minWidth: "40px",
    transition: "all 0.3s ease",
  },

  "& .MuiListItemText-primary": {
    color: isActive ? "#ffffff" : "#e2e8f0",
    fontWeight: isActive ? 600 : 500,
    fontSize: "0.95rem",
    transition: "all 0.3s ease",
  },
}));

const NestedListItemButton = styled(ListItemButton, {
  shouldForwardProp: (prop: string) => prop !== "isActive",
})<{ isActive?: boolean }>(({ theme, isActive }) => ({
  margin: theme.spacing(0.3, 1, 0.3, 3),
  borderRadius: "8px",
  padding: theme.spacing(1, 2),
  color: "#cbd5e1",
  position: "relative",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",

  background: isActive
    ? `linear-gradient(135deg, ${alpha("#6366f1", 0.15)} 0%, ${alpha(
        "#8b5cf6",
        0.1
      )} 100%)`
    : "transparent",

  border: isActive
    ? `1px solid ${alpha("#6366f1", 0.2)}`
    : "1px solid transparent",

  "&::before": {
    content: '""',
    position: "absolute",
    left: "-16px",
    top: "50%",
    transform: "translateY(-50%)",
    width: "12px",
    height: "1px",
    background: alpha("#6366f1", 0.4),
  },

  "&:hover": {
    background: `linear-gradient(135deg, ${alpha("#6366f1", 0.1)} 0%, ${alpha(
      "#8b5cf6",
      0.05
    )} 100%)`,
    border: `1px solid ${alpha("#6366f1", 0.3)}`,
    transform: "translateX(4px)",

    "& .MuiListItemIcon-root": {
      color: "#6366f1",
      transform: "scale(1.1)",
    },

    "& .MuiListItemText-primary": {
      color: "#ffffff",
    },
  },

  "& .MuiListItemIcon-root": {
    color: isActive ? "#6366f1" : "#94a3b8",
    minWidth: "32px",
    fontSize: "1.2rem",
    transition: "all 0.3s ease",
  },

  "& .MuiListItemText-primary": {
    color: isActive ? "#ffffff" : "#cbd5e1",
    fontWeight: isActive ? 600 : 500,
    fontSize: "0.875rem",
    transition: "all 0.3s ease",
  },
}));

const UserProfileBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3, 2),
  background: `
    linear-gradient(135deg, 
      ${alpha("#1e293b", 0.9)} 0%, 
      ${alpha("#334155", 0.8)} 100%
    )
  `,
  borderTop: `1px solid ${alpha("#6366f1", 0.2)}`,
  borderRadius: "20px 20px 0 0",
  margin: theme.spacing(0, 1, 0, 1),
  position: "relative",

  "&::before": {
    content: '""',
    position: "absolute",
    top: "-1px",
    left: "50%",
    transform: "translateX(-50%)",
    width: "40px",
    height: "2px",
    background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
    borderRadius: "2px",
  },
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  width: 48,
  height: 48,
  marginRight: theme.spacing(2),
  border: `2px solid ${alpha("#6366f1", 0.3)}`,
  boxShadow: `0 4px 15px ${alpha("#6366f1", 0.2)}`,
  transition: "all 0.3s ease",

  "&:hover": {
    transform: "scale(1.1)",
    border: `2px solid ${alpha("#6366f1", 0.6)}`,
    boxShadow: `0 6px 20px ${alpha("#6366f1", 0.3)}`,
  },
}));

const LogoutButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(2),
  background: `linear-gradient(135deg, ${alpha("#dc2626", 0.1)} 0%, ${alpha(
    "#ef4444",
    0.05
  )} 100%)`,
  border: `1px solid ${alpha("#dc2626", 0.3)}`,
  color: "#fca5a5",
  fontWeight: 600,
  borderRadius: "12px",
  padding: theme.spacing(1.2, 2),
  textTransform: "none",
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",

  "&:hover": {
    background: `linear-gradient(135deg, ${alpha("#dc2626", 0.2)} 0%, ${alpha(
      "#ef4444",
      0.1
    )} 100%)`,
    border: `1px solid ${alpha("#dc2626", 0.5)}`,
    color: "#ffffff",
    transform: "translateY(-2px)",
    boxShadow: `0 8px 25px ${alpha("#dc2626", 0.3)}`,
  },
}));

// Updated navigation items (removed unused items)
const navItems = [
  { label: "Dashboard", icon: <DashboardIcon />, path: "/dashboard" },
  { label: "Submissions", icon: <ListAltIcon />, path: "/submission" },
  {
    label: "Reports",
    icon: <ReportsIcon />,
    children: [
      { label: "Report Builder", icon: <BuildIcon />, path: "/report-builder" },
      {
        label: "Report History",
        icon: <HistoryIcon />,
        path: "/report-history",
      },
      {
        label: "Templates",
        icon: <TemplatesIcon />,
        path: "/report-templates",
      },
      {
        label: "Google Forms",
        icon: <AutomatedReportsIcon />,
        path: "/google-forms",
      },
    ],
  },
  { label: "Form Builder", icon: <BuildIcon />, path: "/form-builder-admin" },
  { label: "Profile", icon: <PersonIcon />, path: "/profile" },
  { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

export default function EnhancedSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [openReports, setOpenReports] = useState(true);
  const { logout } = useContext(AuthContext);
  const { currentUser, getUserDisplayName, getUserAvatarUrl } = useUser();

  // Use centralized user data with proper fallbacks
  const displayUser = {
    name: currentUser?.display_name || getUserDisplayName(),
    email: currentUser?.email || "user@company.com",
    avatar: currentUser?.avatar_display_url || getUserAvatarUrl(),
  };

  const handleReportsClick = () => {
    setOpenReports((prev: boolean) => !prev);
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

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <StyledDrawer variant="permanent">
      <Box>
        {/* Logo Section */}
        <LogoBox>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 800,
              background:
                "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)",
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: 1,
              mb: 0.5,
            }}
          >
            StratoSys
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: alpha("#e2e8f0", 0.8),
              fontWeight: 500,
              letterSpacing: 2,
              fontSize: "0.75rem",
              textTransform: "uppercase",
            }}
          >
            Report Platform
          </Typography>
        </LogoBox>

        {/* Navigation List */}
        <List sx={{ px: 1, py: 2 }}>
          {navItems.map((item, index) => {
            if (item.children) {
              const isActive = item.children.some(
                (child: { path: string }) => location.pathname === child.path
              );
              return (
                <React.Fragment key={item.label}>
                  <StyledListItemButton
                    onClick={handleReportsClick}
                    isActive={isActive}
                    sx={{
                      animationDelay: `${index * 0.1}s`,
                    }}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} />
                    <Box
                      sx={{
                        color: isActive ? "#6366f1" : "#94a3b8",
                        transition: "all 0.3s ease",
                        transform: openReports
                          ? "rotate(0deg)"
                          : "rotate(-90deg)",
                      }}
                    >
                      <ExpandLess />
                    </Box>
                  </StyledListItemButton>
                  <Collapse in={openReports} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {item.children.map((child, childIndex) => {
                        const childActive = location.pathname === child.path;
                        return (
                          <NestedListItemButton
                            key={child.label}
                            onClick={() => handleNavigation(child.path)}
                            isActive={childActive}
                            sx={{
                              animationDelay: `${
                                (index + childIndex) * 0.1 + 0.2
                              }s`,
                            }}
                          >
                            <ListItemIcon>{child.icon}</ListItemIcon>
                            <ListItemText primary={child.label} />
                          </NestedListItemButton>
                        );
                      })}
                    </List>
                  </Collapse>
                </React.Fragment>
              );
            }

            const isActive = location.pathname === item.path;
            return (
              <StyledListItemButton
                key={item.label}
                onClick={() => handleNavigation(item.path)}
                isActive={isActive}
                sx={{
                  animationDelay: `${index * 0.1}s`,
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </StyledListItemButton>
            );
          })}
        </List>
      </Box>

      {/* Enhanced User Profile Section */}
      <UserProfileBox>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <StyledAvatar src={displayUser.avatar} alt={displayUser.name} />
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="body1"
              sx={{
                color: "#ffffff",
                fontWeight: 700,
                fontSize: "1rem",
                mb: 0.5,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {displayUser.name}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: alpha("#e2e8f0", 0.8),
                fontSize: "0.8rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {displayUser.email}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
          <Chip
            label="Pro"
            size="small"
            sx={{
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "0.7rem",
              height: "22px",
            }}
          />
          <Chip
            label="Online"
            size="small"
            sx={{
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: "0.7rem",
              height: "22px",
            }}
          />
        </Box>

        <LogoutButton
          fullWidth
          onClick={handleLogout}
          startIcon={<LogoutIcon />}
        >
          Sign Out
        </LogoutButton>
      </UserProfileBox>
    </StyledDrawer>
  );
}
