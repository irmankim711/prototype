import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  AppBar,
  Toolbar,
  TextField,
  Checkbox,
  FormControlLabel,
  Divider,
  Chip,
  useMediaQuery,
  styled,
  useTheme,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

// Styled components
const StyledAppBar = styled(AppBar)(() => ({
  backgroundColor: 'transparent',
  backdropFilter: 'blur(10px)',
  boxShadow: 'none',
  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  position: 'sticky',
  top: 0,
  zIndex: 100,
  transition: 'all 0.3s ease',
}));

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  padding: theme.spacing(1.5, 3),
  transition: 'all 0.3s ease',
}));

const NavButton = styled(Button)(() => ({
  color: '#334155',
  textTransform: 'none',
  fontWeight: 500,
  position: 'relative',
  overflow: 'hidden',
  padding: '8px 16px',
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: 0,
    width: '0%',
    height: '2px',
    backgroundColor: '#0e1c40',
    transition: 'width 0.3s ease',
  },
  '&:hover': {
    backgroundColor: 'transparent',
    color: '#0e1c40',
    '&::after': {
      width: '100%',
    },
  },
}));

const RegisterButton = styled(Button)(({ theme }) => ({
  backgroundColor: '#0e1c40',
  color: 'white',
  textTransform: 'none',
  fontWeight: 500,
  padding: theme.spacing(1, 3),
  borderRadius: '8px',
  boxShadow: '0 4px 14px rgba(14, 28, 64, 0.2)',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: '#192e5b',
    transform: 'translateY(-3px)',
    boxShadow: '0 6px 20px rgba(14, 28, 64, 0.3)',
  },
}));

const HeroSection = styled(Box)(({ theme }) => ({
  backgroundColor: '#f8fafc',
  background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
  padding: theme.spacing(12, 0, 8),
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '-10%',
    right: '-5%',
    width: '500px',
    height: '500px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(58, 89, 152, 0.1) 0%, rgba(14, 28, 64, 0.05) 70%)',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '-15%',
    left: '-10%',
    width: '600px',
    height: '600px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(14, 28, 64, 0.08) 0%, rgba(58, 89, 152, 0.03) 70%)',
  },
}));

const FeatureCard = styled(Box)(({ theme }) => ({
  background: 'rgba(255, 255, 255, 0.7)',
  backdropFilter: 'blur(10px)',
  borderRadius: '16px',
  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
  padding: theme.spacing(3),
  transition: 'all 0.3s ease',
  border: '1px solid rgba(255, 255, 255, 0.2)',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  '&:hover': {
    transform: 'translateY(-10px)',
    boxShadow: '0 15px 35px rgba(14, 28, 64, 0.1)',
    border: '1px solid rgba(58, 89, 152, 0.3)',
  },
}));

const AnimatedIcon = styled(Box)(({ theme }) => ({
  width: '60px',
  height: '60px',
  borderRadius: '12px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '24px',
  marginBottom: theme.spacing(2),
  background: 'linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%)',
  boxShadow: '0 8px 16px rgba(14, 28, 64, 0.1)',
  transition: 'all 0.3s ease',
  color: '#0e1c40',
  '&:hover': {
    transform: 'rotate(5deg) scale(1.1)',
  },
}));

const LoginCard = styled(Card)(({ theme }) => ({
  maxWidth: 450,
  margin: '0 auto',
  padding: theme.spacing(4),
  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
  borderRadius: '20px',
  background: 'rgba(255, 255, 255, 0.95)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.2)',
  transition: 'all 0.3s ease',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  '& .MuiOutlinedInput-root': {
    borderRadius: '10px',
    '& fieldset': {
      borderColor: 'rgba(0, 0, 0, 0.1)',
    },
    '&:hover fieldset': {
      borderColor: '#0e1c40',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#0e1c40',
    },
  },
  '& .MuiInputLabel-root': {
    color: '#64748b',
    '&.Mui-focused': {
      color: '#0e1c40',
    },
  },
  '& .MuiInputBase-input': {
    padding: '14px 16px',
  },
}));

// Main component
export default function LandingPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  const handleLogin = () => {
    localStorage.setItem('isAuthenticated', 'true');
    navigate('/dashboard');
  };
  
  const handleShowLogin = () => {
    setShowLogin(true);
  };
  
  const handleBackToHome = () => {
    setShowLogin(false);
  };
  
  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');
    
    // Simulating API call
    setTimeout(() => {
      setLoading(false);
      if (email === 'admin@stratosys.com' && password === 'password') {
        localStorage.setItem('isAuthenticated', 'true');
        navigate('/dashboard');
      } else {
        setErrorMessage('Invalid email or password');
      }
    }, 1500);
  };
  
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation */}
      <StyledAppBar>
        <StyledToolbar>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#0e1c40' }}>
            StratoSys Report
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {!isMobile && (
              <>
                <NavButton>
                  Features
                </NavButton>
                <NavButton>
                  Solutions
                </NavButton>
                <NavButton>
                  About Us
                </NavButton>
              </>
            )}
            
            <RegisterButton onClick={handleShowLogin} sx={{ ml: 2 }}>
              Login
            </RegisterButton>
          </Box>
        </StyledToolbar>
      </StyledAppBar>

      {/* Main Content */}
      {!showLogin ? (
        <>
          {/* Hero Section */}
          <HeroSection>
            <Container>
              <Grid container spacing={4} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 4 }}>
                    <Typography 
                      variant="h2" 
                      component="h1" 
                      sx={{ 
                        fontWeight: 700, 
                        color: '#0e1c40',
                        mb: 2,
                        fontSize: { xs: '2.5rem', md: '3.5rem' } 
                      }}
                    >
                      StratoSys Report Automation
                    </Typography>
                    <Typography 
                      variant="h5" 
                      sx={{ 
                        color: '#64748b',
                        mb: 4,
                        fontWeight: 400,
                        lineHeight: 1.5 
                      }}
                    >
                      Streamline your reporting workflow with automated data processing and advanced visualizations
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      <RegisterButton 
                        onClick={handleShowLogin}
                        size="large" 
                        sx={{ px: 4, py: 1.5 }}
                      >
                        Get Started
                      </RegisterButton>
                      <Button 
                        variant="outlined" 
                        size="large"
                        sx={{ 
                          borderColor: '#0e1c40', 
                          color: '#0e1c40',
                          px: 4,
                          py: 1.5,
                          '&:hover': {
                            borderColor: '#192e5b',
                            backgroundColor: 'rgba(14, 28, 64, 0.05)'
                          }
                        }}
                      >
                        Learn More
                      </Button>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box
                    component="img"
                    src="https://i.imgur.com/RK1AVsJ.png"
                    alt="Dashboard Preview"
                    sx={{
                      width: '100%',
                      height: 'auto',
                      borderRadius: '16px',
                      boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
                      transform: { md: 'perspective(1000px) rotateY(-5deg) rotateX(5deg)' },
                      transition: 'all 0.5s ease',
                      '&:hover': {
                        transform: { md: 'perspective(1000px) rotateY(-2deg) rotateX(2deg) translateY(-10px)' },
                        boxShadow: '0 30px 50px rgba(0, 0, 0, 0.2)',
                      },
                    }}
                  />
                </Grid>
              </Grid>
            </Container>
          </HeroSection>

          {/* Features Section */}
          <Box sx={{ py: 10, backgroundColor: '#fff' }}>
            <Container>
              <Typography 
                variant="h3" 
                component="h2" 
                align="center" 
                sx={{ fontWeight: 700, mb: 6, color: '#0e1c40' }}
              >
                Powerful Features
              </Typography>
              
              <Grid container spacing={4}>
                <Grid item xs={12} md={4}>
                  <FeatureCard>
                    <AnimatedIcon>
                      <i className="fas fa-chart-line" />
                    </AnimatedIcon>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 2, color: '#0e1c40' }}>
                      Advanced Analytics
                    </Typography>
                    <Typography variant="body1" sx={{ color: '#64748b', mb: 2, flexGrow: 1 }}>
                      Gain deep insights through comprehensive data analysis and visualization tools designed for strategic decision-making.
                    </Typography>
                    <Button 
                      variant="text" 
                      sx={{ 
                        color: '#0e1c40', 
                        p: 0,
                        '&:hover': { backgroundColor: 'transparent', textDecoration: 'underline' } 
                      }}
                    >
                      Learn more →
                    </Button>
                  </FeatureCard>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FeatureCard>
                    <AnimatedIcon>
                      <i className="fas fa-robot" />
                    </AnimatedIcon>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 2, color: '#0e1c40' }}>
                      Automated Reporting
                    </Typography>
                    <Typography variant="body1" sx={{ color: '#64748b', mb: 2, flexGrow: 1 }}>
                      Schedule and generate reports automatically, saving time and ensuring consistent delivery to stakeholders.
                    </Typography>
                    <Button 
                      variant="text" 
                      sx={{ 
                        color: '#0e1c40', 
                        p: 0,
                        '&:hover': { backgroundColor: 'transparent', textDecoration: 'underline' } 
                      }}
                    >
                      Learn more →
                    </Button>
                  </FeatureCard>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FeatureCard>
                    <AnimatedIcon>
                      <i className="fas fa-lock" />
                    </AnimatedIcon>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 2, color: '#0e1c40' }}>
                      Secure Data Handling
                    </Typography>
                    <Typography variant="body1" sx={{ color: '#64748b', mb: 2, flexGrow: 1 }}>
                      Enterprise-grade security protocols to protect sensitive information with role-based access controls.
                    </Typography>
                    <Button 
                      variant="text" 
                      sx={{ 
                        color: '#0e1c40', 
                        p: 0,
                        '&:hover': { backgroundColor: 'transparent', textDecoration: 'underline' } 
                      }}
                    >
                      Learn more →
                    </Button>
                  </FeatureCard>
                </Grid>
              </Grid>
            </Container>
          </Box>

          {/* Footer */}
          <Box sx={{ bgcolor: '#f8fafc', py: 4, borderTop: '1px solid #e2e8f0' }}>
            <Container>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="h6" sx={{ color: '#1e3a8a', fontWeight: 600, mb: 2 }}>
                    StratoSys Report
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Transforming report automation with innovative solutions.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Quick Links
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                      About Us
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                      Features
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                      Privacy Policy
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                      Terms of Service
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Contact Us
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                    Email: contact@stratosys.com
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Phone: +60 12-345-6789
                  </Typography>
                </Grid>
              </Grid>
              <Divider sx={{ my: 4 }} />
              <Typography variant="body2" color="textSecondary" align="center">
                {new Date().getFullYear()} StratoSys Report. All rights reserved.
              </Typography>
            </Container>
          </Box>
        </>
      ) : (
        <Box sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 8,
          backgroundColor: '#f8fafc' 
        }}>
          <LoginCard>
            <Box sx={{ mb: 4, textAlign: 'center' }}>
              <Typography variant="h4" component="h1" sx={{ fontWeight: 700, color: '#0e1c40', mb: 1 }}>
                Welcome Back
              </Typography>
              <Typography variant="body1" color="textSecondary">
                Log in to your StratoSys Report account
              </Typography>
            </Box>
            
            {errorMessage && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {errorMessage}
              </Alert>
            )}
            
            <form onSubmit={handleLoginSubmit}>
              <StyledTextField
                label="Email Address"
                variant="outlined"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                type="email"
                placeholder="your@email.com"
              />
              
              <StyledTextField
                label="Password"
                variant="outlined"
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                type="password"
                placeholder="Enter your password"
              />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <FormControlLabel
                  control={
                    <Checkbox 
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      sx={{ 
                        color: '#0e1c40',
                        '&.Mui-checked': { color: '#0e1c40' } 
                      }}
                    />
                  }
                  label="Remember me"
                />
                
                <Typography variant="body2" sx={{ color: '#0e1c40', cursor: 'pointer' }}>
                  Forgot password?
                </Typography>
              </Box>
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.5,
                  backgroundColor: '#0e1c40',
                  '&:hover': { backgroundColor: '#192e5b' },
                  mb: 2,
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
              </Button>
              
              <Button
                variant="outlined"
                fullWidth
                onClick={handleBackToHome}
                sx={{
                  py: 1.5,
                  borderColor: '#0e1c40',
                  color: '#0e1c40',
                  '&:hover': {
                    borderColor: '#192e5b',
                    backgroundColor: 'rgba(14, 28, 64, 0.05)'
                  }
                }}
              >
                Back to Home
              </Button>
            </form>
          </LoginCard>
        </Box>
      )}
    </Box>
  );
}
