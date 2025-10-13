import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Avatar,
  Chip,
  alpha,
  Fade,
  Slide,
  IconButton,
  Paper,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import {
  ArrowForward,
  Security,
  AutoAwesome,
  TrendingUp,
  Groups,
  Email,
  Phone,
  LinkedIn,
  Twitter,
} from "@mui/icons-material";

export default function AboutUs() {
  const navigate = useNavigate();
  const [animationTrigger, setAnimationTrigger] = useState(false);

  useEffect(() => {
    setAnimationTrigger(true);
  }, []);

  const features = [
    {
      icon: <AutoAwesome />,
      title: "AI-Powered Intelligence",
      description:
        "Advanced machine learning algorithms that transform raw data into actionable insights automatically.",
      color: "#6366f1",
      delay: 100,
    },
    {
      icon: <Security />,
      title: "Enterprise Security",
      description:
        "Bank-grade encryption and compliance standards protecting your most sensitive business data.",
      color: "#10b981",
      delay: 200,
    },
    {
      icon: <TrendingUp />,
      title: "Infinite Scalability",
      description:
        "Cloud-native architecture that grows seamlessly from startup to global enterprise scale.",
      color: "#f59e0b",
      delay: 300,
    },
    {
      icon: <Groups />,
      title: "Human-Centered Design",
      description:
        "Intuitive interfaces designed around real user workflows and cognitive psychology principles.",
      color: "#ec4899",
      delay: 400,
    },
  ];

  const team = [
    {
      name: "Irman",
      role: "Software Architect",
      avatar: "I",
      bio: "Visionary architect with 8+ years designing scalable enterprise systems.",
      color: "#6366f1",
      social: { linkedin: "#", twitter: "#" },
    },
    {
      name: "Asmaan",
      role: "UI/UX Designer",
      avatar: "A",
      bio: "Design thinking expert crafting user experiences that delight and convert.",
      color: "#10b981",
      social: { linkedin: "#", twitter: "#" },
    },
    {
      name: "Abdul Muiz",
      role: "Backend Developer",
      avatar: "M",
      bio: "Performance optimization specialist building lightning-fast backend systems.",
      color: "#f59e0b",
      social: { linkedin: "#", twitter: "#" },
    },
  ];

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: `linear-gradient(135deg, ${alpha(
          "#0e1c40",
          0.05
        )} 0%, ${alpha("#6366f1", 0.05)} 100%)`,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Pattern */}
      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `radial-gradient(circle at 25% 25%, ${alpha(
            "#6366f1",
            0.1
          )} 0%, transparent 50%),
                            radial-gradient(circle at 75% 75%, ${alpha(
                              "#10b981",
                              0.1
                            )} 0%, transparent 50%)`,
          pointerEvents: "none",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative", py: 8 }}>
        {/* Hero Section */}
        <Fade in={animationTrigger} timeout={800}>
          <Box sx={{ textAlign: "center", mb: 8 }}>
            <Chip
              label="🚀 Next-Generation Reporting"
              sx={{
                mb: 3,
                backgroundColor: alpha("#6366f1", 0.1),
                color: "#6366f1",
                fontWeight: 600,
                fontSize: "0.9rem",
                borderRadius: "20px",
                px: 2,
                py: 1,
              }}
            />
            <Typography
              variant="h1"
              sx={{
                fontWeight: 800,
                fontSize: { xs: "2.5rem", md: "3.5rem", lg: "4rem" },
                background: `linear-gradient(135deg, #0e1c40 0%, #6366f1 100%)`,
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                mb: 3,
                lineHeight: 1.2,
              }}
            >
              About StratoSys
            </Typography>
            <Typography
              variant="h4"
              sx={{
                color: "#64748b",
                fontWeight: 400,
                maxWidth: "800px",
                mx: "auto",
                lineHeight: 1.5,
                mb: 4,
              }}
            >
              Transforming enterprise reporting with{" "}
              <Box
                component="span"
                sx={{
                  color: "#6366f1",
                  fontWeight: 600,
                  position: "relative",
                  "&::after": {
                    content: '""',
                    position: "absolute",
                    bottom: -2,
                    left: 0,
                    right: 0,
                    height: 3,
                    background: `linear-gradient(90deg, #6366f1, #10b981)`,
                    borderRadius: 1,
                  },
                }}
              >
                AI, automation, and modern UX
              </Box>
            </Typography>
          </Box>
        </Fade>

        {/* Mission & Vision */}
        <Slide direction="up" in={animationTrigger} timeout={1000}>
          <Grid container spacing={4} sx={{ mb: 8 }}>
            <Grid item xs={12} md={6}>
              <Paper
                elevation={0}
                sx={{
                  p: 4,
                  height: "100%",
                  background: `linear-gradient(135deg, ${alpha(
                    "#6366f1",
                    0.05
                  )} 0%, transparent 100%)`,
                  border: `2px solid ${alpha("#6366f1", 0.1)}`,
                  borderRadius: "20px",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    transform: "translateY(-8px)",
                    boxShadow: `0 20px 40px ${alpha("#6366f1", 0.15)}`,
                    border: `2px solid ${alpha("#6366f1", 0.2)}`,
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    mb: 3,
                  }}
                >
                  <Avatar
                    sx={{
                      backgroundColor: "#6366f1",
                      color: "white",
                      mr: 2,
                      width: 48,
                      height: 48,
                    }}
                  >
                    🎯
                  </Avatar>
                  <Typography
                    variant="h5"
                    sx={{
                      color: "#0e1c40",
                      fontWeight: 700,
                    }}
                  >
                    Our Mission
                  </Typography>
                </Box>
                <Typography
                  sx={{
                    color: "#475569",
                    fontSize: "1.1rem",
                    lineHeight: 1.7,
                  }}
                >
                  Empower organizations to make data-driven decisions with
                  confidence and ease by automating and modernizing the
                  reporting process through cutting-edge technology.
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper
                elevation={0}
                sx={{
                  p: 4,
                  height: "100%",
                  background: `linear-gradient(135deg, ${alpha(
                    "#10b981",
                    0.05
                  )} 0%, transparent 100%)`,
                  border: `2px solid ${alpha("#10b981", 0.1)}`,
                  borderRadius: "20px",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    transform: "translateY(-8px)",
                    boxShadow: `0 20px 40px ${alpha("#10b981", 0.15)}`,
                    border: `2px solid ${alpha("#10b981", 0.2)}`,
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    mb: 3,
                  }}
                >
                  <Avatar
                    sx={{
                      backgroundColor: "#10b981",
                      color: "white",
                      mr: 2,
                      width: 48,
                      height: 48,
                    }}
                  >
                    🌟
                  </Avatar>
                  <Typography
                    variant="h5"
                    sx={{
                      color: "#0e1c40",
                      fontWeight: 700,
                    }}
                  >
                    Our Vision
                  </Typography>
                </Box>
                <Typography
                  sx={{
                    color: "#475569",
                    fontSize: "1.1rem",
                    lineHeight: 1.7,
                  }}
                >
                  To be the global leader in secure, scalable, and user-friendly
                  reporting solutions powered by AI and seamless integrations
                  across all business ecosystems.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Slide>

        {/* Features Section */}
        <Box sx={{ mb: 8 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              color: "#0e1c40",
              textAlign: "center",
              mb: 6,
            }}
          >
            Why Choose StratoSys?
          </Typography>
          <Grid container spacing={4}>
            {features.map((feature: any) => (
              <Grid item xs={12} md={6} key={feature.title}>
                <Slide
                  direction="up"
                  in={animationTrigger}
                  timeout={1000 + feature.delay}
                >
                  <Card
                    elevation={0}
                    sx={{
                      p: 3,
                      height: "100%",
                      background: `linear-gradient(135deg, ${alpha(
                        feature.color,
                        0.05
                      )} 0%, transparent 100%)`,
                      border: `2px solid ${alpha(feature.color, 0.1)}`,
                      borderRadius: "16px",
                      transition: "all 0.3s ease",
                      cursor: "pointer",
                      "&:hover": {
                        transform: "translateY(-8px)",
                        boxShadow: `0 20px 40px ${alpha(feature.color, 0.15)}`,
                        border: `2px solid ${alpha(feature.color, 0.3)}`,
                      },
                    }}
                  >
                    <CardContent sx={{ p: 0 }}>
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "flex-start",
                          mb: 2,
                        }}
                      >
                        <Avatar
                          sx={{
                            backgroundColor: feature.color,
                            color: "white",
                            mr: 2,
                            width: 56,
                            height: 56,
                          }}
                        >
                          {feature.icon}
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: "#0e1c40",
                              mb: 1,
                            }}
                          >
                            {feature.title}
                          </Typography>
                          <Typography
                            sx={{
                              color: "#64748b",
                              lineHeight: 1.6,
                            }}
                          >
                            {feature.description}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Slide>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Team Section */}
        <Box sx={{ mb: 8 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              color: "#0e1c40",
              textAlign: "center",
              mb: 2,
            }}
          >
            Meet Our Team
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: "#64748b",
              textAlign: "center",
              mb: 6,
              maxWidth: "600px",
              mx: "auto",
            }}
          >
            Passionate professionals dedicated to revolutionizing how businesses
            handle data and reporting
          </Typography>
          <Grid container spacing={4} justifyContent="center">
            {team.map((member, index) => (
              <Grid item xs={12} sm={6} md={4} key={member.name}>
                <Slide
                  direction="up"
                  in={animationTrigger}
                  timeout={1200 + index * 150}
                >
                  <Card
                    elevation={0}
                    sx={{
                      textAlign: "center",
                      p: 3,
                      background: `linear-gradient(135deg, ${alpha(
                        member.color,
                        0.05
                      )} 0%, transparent 100%)`,
                      border: `2px solid ${alpha(member.color, 0.1)}`,
                      borderRadius: "20px",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        transform: "translateY(-12px)",
                        boxShadow: `0 25px 50px ${alpha(member.color, 0.15)}`,
                        border: `2px solid ${alpha(member.color, 0.3)}`,
                      },
                    }}
                  >
                    <CardContent>
                      <Avatar
                        sx={{
                          bgcolor: member.color,
                          mx: "auto",
                          width: 80,
                          height: 80,
                          fontSize: "2rem",
                          fontWeight: 700,
                          mb: 2,
                          border: `4px solid ${alpha(member.color, 0.2)}`,
                        }}
                      >
                        {member.avatar}
                      </Avatar>
                      <Typography
                        variant="h6"
                        sx={{ fontWeight: 700, color: "#0e1c40", mb: 1 }}
                      >
                        {member.name}
                      </Typography>
                      <Chip
                        label={member.role}
                        sx={{
                          backgroundColor: alpha(member.color, 0.1),
                          color: member.color,
                          fontWeight: 600,
                          mb: 2,
                        }}
                      />
                      <Typography
                        variant="body2"
                        sx={{
                          color: "#64748b",
                          lineHeight: 1.5,
                          mb: 3,
                        }}
                      >
                        {member.bio}
                      </Typography>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "center",
                          gap: 1,
                        }}
                      >
                        <IconButton
                          size="small"
                          sx={{
                            backgroundColor: alpha(member.color, 0.1),
                            color: member.color,
                            "&:hover": {
                              backgroundColor: member.color,
                              color: "white",
                            },
                          }}
                        >
                          <LinkedIn fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          sx={{
                            backgroundColor: alpha(member.color, 0.1),
                            color: member.color,
                            "&:hover": {
                              backgroundColor: member.color,
                              color: "white",
                            },
                          }}
                        >
                          <Twitter fontSize="small" />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </Slide>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Contact Section */}
        <Slide direction="up" in={animationTrigger} timeout={1600}>
          <Box
            sx={{
              textAlign: "center",
              p: 6,
              background: `linear-gradient(135deg, ${alpha(
                "#0e1c40",
                0.05
              )} 0%, ${alpha("#6366f1", 0.05)} 100%)`,
              borderRadius: "24px",
              border: `2px solid ${alpha("#6366f1", 0.1)}`,
              mb: 6,
            }}
          >
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                color: "#0e1c40",
                mb: 2,
              }}
            >
              Let's Connect
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: "#64748b",
                mb: 4,
                maxWidth: "500px",
                mx: "auto",
              }}
            >
              Ready to transform your reporting workflow? Get in touch with our
              team
            </Typography>
            <Grid container spacing={3} justifyContent="center" sx={{ mb: 4 }}>
              <Grid item>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    p: 2,
                    backgroundColor: alpha("#6366f1", 0.1),
                    borderRadius: "12px",
                    color: "#6366f1",
                  }}
                >
                  <Email />
                  <Typography fontWeight={600}>
                    contact@stratosys.com
                  </Typography>
                </Box>
              </Grid>
              <Grid item>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    p: 2,
                    backgroundColor: alpha("#10b981", 0.1),
                    borderRadius: "12px",
                    color: "#10b981",
                  }}
                >
                  <Phone />
                  <Typography fontWeight={600}>+60 12-345-6789</Typography>
                </Box>
              </Grid>
            </Grid>
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForward />}
              onClick={() => navigate("/")}
              sx={{
                px: 4,
                py: 1.5,
                fontWeight: 700,
                fontSize: "1.1rem",
                borderRadius: "12px",
                background: `linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)`,
                boxShadow: `0 8px 24px ${alpha("#6366f1", 0.3)}`,
                textTransform: "none",
                "&:hover": {
                  background: `linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)`,
                  transform: "translateY(-2px)",
                  boxShadow: `0 12px 32px ${alpha("#6366f1", 0.4)}`,
                },
              }}
            >
              Back to Home
            </Button>
          </Box>
        </Slide>
      </Container>
    </Box>
  );
}
