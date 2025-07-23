import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  Container,
  Divider,
  Grid,
  Typography,
  AppBar,
  Toolbar,
  TextField,
  Checkbox,
  FormControlLabel,
  useMediaQuery,
  styled,
  useTheme,
  Alert,
  CircularProgress,
  Modal,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../../services/api';
import React from 'react';

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
  const [showSignup, setShowSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirm, setSignupConfirm] = useState('');
  const [signupLoading, setSignupLoading] = useState(false);
  const [signupError, setSignupError] = useState('');
  const [signupSuccess, setSignupSuccess] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  
  const handleShowLogin = () => {
    setShowLogin(true);
    setShowSignup(false);
  };
  const handleShowSignup = () => {
    setShowSignup(true);
    setShowLogin(false);
  };
  const handleBackToHome = () => {
    setShowLogin(false);
    setShowSignup(false);
  };
  
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');
    try {
      const response = await login({ email, password });
      if (response.access_token) {
        localStorage.setItem('token', response.access_token);
        navigate('/dashboard');
      } else {
        setErrorMessage('Login failed. No token received.');
      }
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.msg || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  // Signup handler
  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignupError('');
    setSignupSuccess(false);
    if (!signupEmail || !signupPassword || !signupConfirm) {
      setSignupError('All fields are required.');
      return;
    }
    if (signupPassword !== signupConfirm) {
      setSignupError('Passwords do not match.');
      return;
    }
    setSignupLoading(true);
    try {
      await register({ email: signupEmail, password: signupPassword, confirmPassword: signupConfirm });
      setSignupSuccess(true);
      setSignupEmail('');
      setSignupPassword('');
      setSignupConfirm('');
    } catch (err: any) {
      setSignupError(err?.response?.data?.msg || 'Registration failed.');
    } finally {
      setSignupLoading(false);
    }
  };
  
  // Section refs for smooth scroll
  const featuresRef = React.useRef<HTMLDivElement>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<'solutions' | 'learn' | null>(null);

  // Scroll handlers
  const scrollToSection = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Modal openers
  const handleOpenModal = (content: 'solutions' | 'learn') => {
    setModalContent(content);
    setModalOpen(true);
  };
  const handleCloseModal = () => setModalOpen(false);
  
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
                <NavButton onClick={() => scrollToSection(featuresRef)}>Features</NavButton>
                <NavButton onClick={() => handleOpenModal('solutions')}>Solutions</NavButton>
                <NavButton onClick={() => handleOpenModal('learn')}>Learn More</NavButton>
              </>
            )}
            <RegisterButton onClick={handleShowLogin} sx={{ ml: 2 }}>
              Login
            </RegisterButton>
            <Button onClick={handleShowSignup} sx={{ ml: 2, color: '#0e1c40', fontWeight: 500 }}>
              Sign up
            </Button>
          </Box>
        </StyledToolbar>
      </StyledAppBar>
      {/* Main Content */}
      {(!showLogin && !showSignup) ? (
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
                      sx={{ fontWeight: 700, color: '#0e1c40', mb: 2, fontSize: { xs: '2.5rem', md: '3.5rem' } }}
                    >
                      StratoSys Report Automation
                    </Typography>
                    <Typography 
                      variant="h5" 
                      sx={{ color: '#64748b', mb: 4, fontWeight: 400, lineHeight: 1.5 }}
                    >
                      Streamline your reporting workflow with automated data processing and advanced visualizations
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      <RegisterButton onClick={handleShowLogin} size="large" sx={{ px: 4, py: 1.5 }}>
                        Get Started
                      </RegisterButton>
                      <Button variant="outlined" size="large" sx={{ borderColor: '#0e1c40', color: '#0e1c40', px: 4, py: 1.5, '&:hover': { borderColor: '#192e5b', backgroundColor: 'rgba(14, 28, 64, 0.05)' } }} onClick={() => handleOpenModal('learn')}>
                        Learn More
                      </Button>
                      <Button onClick={handleShowSignup} size="large" sx={{ color: '#0e1c40', fontWeight: 500, px: 4, py: 1.5 }}>
                        Sign up
                      </Button>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box
                    component="img"
                    src="https://i.imgur.com/RK1AVsJ.png"
                    alt="Dashboard Preview"
                    sx={{ width: '100%', height: 'auto', borderRadius: '16px', boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)', transform: { md: 'perspective(1000px) rotateY(-5deg) rotateX(5deg)' }, transition: 'all 0.5s ease', '&:hover': { transform: { md: 'perspective(1000px) rotateY(-2deg) rotateX(2deg) translateY(-10px)' }, boxShadow: '0 30px 50px rgba(0, 0, 0, 0.2)' }, }}
                  />
                </Grid>
              </Grid>
            </Container>
          </HeroSection>

          {/* Features Section */}
          <Box ref={featuresRef} sx={{ py: 10, backgroundColor: '#fff' }}>
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
                      onClick={() => handleOpenModal('learn')}
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
                      onClick={() => handleOpenModal('learn')}
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
                      onClick={() => handleOpenModal('learn')}
                    >
                      Learn more →
                    </Button>
                  </FeatureCard>
                </Grid>
              </Grid>
            </Container>
          </Box>

          {/* Solutions Modal */}
          <Modal open={modalOpen} onClose={handleCloseModal} aria-labelledby="modal-title" aria-describedby="modal-desc">
            <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper', boxShadow: 24, p: 4, borderRadius: 2, minWidth: 320, maxWidth: 480 }}>
              {modalContent === 'solutions' && (
                <>
                  <Typography id="modal-title" variant="h6" sx={{ mb: 2 }}>Solutions</Typography>
                  <Typography id="modal-desc" sx={{ color: 'text.secondary' }}>
                    We offer end-to-end solutions for report automation, data integration, and analytics. From custom form builders to real-time dashboards and secure exports, StratoSys adapts to your workflow and scales with your needs.
                  </Typography>
                </>
              )}
              {modalContent === 'learn' && (
                <>
                  <Typography id="modal-title" variant="h6" sx={{ mb: 2 }}>Learn More</Typography>
                  <Typography id="modal-desc" sx={{ color: 'text.secondary' }}>
                    Discover how StratoSys leverages AI, automation, and modern UX to deliver enterprise-grade reporting. Contact us for a personalized demo or explore our documentation for technical details.
                  </Typography>
                </>
              )}
              <Button onClick={handleCloseModal} sx={{ mt: 3, color: '#0e1c40', fontWeight: 600 }} fullWidth>Close</Button>
            </Box>
          </Modal>

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
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }} onClick={() => navigate('/about')}>
                      About Us
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }} onClick={() => scrollToSection(featuresRef)}>
                      Features
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }} onClick={() => handleOpenModal('solutions')}>
                      Solutions
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }} onClick={() => handleOpenModal('learn')}>
                      Learn More
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
      ) : null}
      {/* Login/Signup Card */}
      {(showLogin || showSignup) && (
        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', py: 8 }}>
          <LoginCard>
            <Box sx={{ mb: 3, textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#0e1c40' }}>
                {showLogin ? 'Login to StratoSys' : 'Create your StratoSys account'}
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>
                {showLogin ? 'Welcome back! Please login to your account.' : 'Sign up to get started with automated reporting.'}
              </Typography>
            </Box>
            {showLogin && (
              <form onSubmit={handleLoginSubmit}>
                <StyledTextField
                  label="Email"
                  type="email"
                  fullWidth
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
                <StyledTextField
                  label="Password"
                  type="password"
                  fullWidth
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <FormControlLabel
                  control={<Checkbox checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} />}
                  label="Remember me"
                  sx={{ mb: 2 }}
                />
                {errorMessage && <Alert severity="error" sx={{ mb: 2 }}>{errorMessage}</Alert>}
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  sx={{ py: 1.5, fontWeight: 600, fontSize: '1rem', borderRadius: '10px', mb: 2 }}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Login'}
                </Button>
                <Button fullWidth sx={{ color: '#0e1c40', fontWeight: 500 }} onClick={handleShowSignup}>
                  Don't have an account? Sign up
                </Button>
                <Button fullWidth sx={{ color: '#64748b', mt: 1 }} onClick={handleBackToHome}>
                  Back to Home
                </Button>
              </form>
            )}
            {showSignup && (
              <form onSubmit={handleSignupSubmit}>
                <StyledTextField
                  label="Email"
                  type="email"
                  fullWidth
                  value={signupEmail}
                  onChange={e => setSignupEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
                <StyledTextField
                  label="Password"
                  type="password"
                  fullWidth
                  value={signupPassword}
                  onChange={e => setSignupPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                />
                <StyledTextField
                  label="Confirm Password"
                  type="password"
                  fullWidth
                  value={signupConfirm}
                  onChange={e => setSignupConfirm(e.target.value)}
                  required
                />
                {signupError && <Alert severity="error" sx={{ mb: 2 }}>{signupError}</Alert>}
                {signupSuccess && <Alert severity="success" sx={{ mb: 2 }}>Registration successful! You can now log in.</Alert>}
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  sx={{ py: 1.5, fontWeight: 600, fontSize: '1rem', borderRadius: '10px', mb: 2 }}
                  disabled={signupLoading}
                >
                  {signupLoading ? <CircularProgress size={24} /> : 'Sign up'}
                </Button>
                <Button fullWidth sx={{ color: '#0e1c40', fontWeight: 500 }} onClick={handleShowLogin}>
                  Already have an account? Login
                </Button>
                <Button fullWidth sx={{ color: '#64748b', mt: 1 }} onClick={handleBackToHome}>
                  Back to Home
                </Button>
              </form>
            )}
          </LoginCard>
        </Box>
      )}
    </Box>
  );
}
