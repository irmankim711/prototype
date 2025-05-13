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

// Custom styled components

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

const ProjectCard = styled(Card)(() => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  borderRadius: '16px',
  overflow: 'hidden',
  background: 'rgba(255, 255, 255, 0.8)',
  backdropFilter: 'blur(10px)',
  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  '&:hover': {
    transform: 'translateY(-12px) rotateZ(1deg)',
    boxShadow: '0 20px 40px rgba(14, 28, 64, 0.15)',
    '& .project-image': {
      transform: 'scale(1.05)',
    },
  },
}));

const ViewProjectButton = styled(Button)(() => ({
  backgroundColor: '#0e1c40',
  color: 'white',
  textTransform: 'none',
  fontWeight: 600,
  marginTop: 'auto',
  borderRadius: '8px',
  padding: '10px 16px',
  boxShadow: '0 4px 12px rgba(14, 28, 64, 0.2)',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: '#192e5b',
    transform: 'translateY(-3px)',
    boxShadow: '0 8px 16px rgba(14, 28, 64, 0.3)',
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
  overflow: 'hidden',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '5px',
    background: 'linear-gradient(90deg, #0e1c40, #3a5998)',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: '150px',
    height: '150px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(58, 89, 152, 0.05) 0%, rgba(255, 255, 255, 0) 70%)',
    zIndex: 0,
  },
}));

const AnimatedProjectImage = styled(Box)(() => ({
  overflow: 'hidden',
  borderTopLeftRadius: '16px',
  borderTopRightRadius: '16px',
  '& img': {
    transition: 'transform 0.5s ease',
    width: '100%',
    height: '160px',
    objectFit: 'cover',
  },
}));

const ProjectTag = styled(Chip)(() => ({
  fontSize: '0.75rem',
  fontWeight: 500,
  height: '26px',
  marginRight: '6px',
  marginBottom: '6px',
  background: 'rgba(14, 28, 64, 0.06)',
  color: '#0e1c40',
  transition: 'all 0.3s ease',
  '&:hover': {
    background: 'rgba(14, 28, 64, 0.1)',
    transform: 'translateY(-2px)',
  },
}));

const StyledInput = styled(TextField)(() => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: '10px',
    transition: 'all 0.3s ease',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
    },
    '&.Mui-focused': {
      backgroundColor: 'white',
      boxShadow: '0 0 0 2px rgba(14, 28, 64, 0.2)',
    },
    '& fieldset': {
      borderColor: 'rgba(14, 28, 64, 0.1)',
    },
    '&:hover fieldset': {
      borderColor: 'rgba(14, 28, 64, 0.3)',
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

const GoogleIcon = () => (
  <Box component="img" src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" sx={{ width: 18, height: 18, mr: 1 }} />
);

const MicrosoftIcon = () => (
  <Box component="img" src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/512px-Microsoft_logo.svg.png" alt="Microsoft" sx={{ width: 18, height: 18, mr: 1 }} />
);

function LandingPage() {
  // State for the login/register UI
  const [showLogin, setShowLogin] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fullName, setFullName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Dummy test credentials
  const TEST_EMAIL = 'test@stratosys.com';
  const TEST_PASSWORD = 'Password123';

  const navigate = useNavigate();
  const isMobile = useMediaQuery(useTheme().breakpoints.down('sm'));

  // Handle navigation and form submission
  

  const handleLogin = () => {
    setShowLogin(true);
  };

  const handleRegister = () => {
    setShowLogin(true);
    setIsLoginMode(false);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Simple validation
    if (!email) {
      setError('Email is required');
      setLoading(false);
      return;
    }

    if (!password) {
      setError('Password is required');
      setLoading(false);
      return;
    }

    // Demo login check with test credentials
    if (isLoginMode) {
      setTimeout(() => {
        if (email === TEST_EMAIL && password === TEST_PASSWORD) {
          // Store in localStorage to maintain session
          localStorage.setItem('isAuthenticated', 'true');
          localStorage.setItem('user', JSON.stringify({ email, name: 'Test User' }));
          navigate('/dashboard');
        } else {
          setError('Invalid credentials. Try test@stratosys.com / Password123');
        }
        setLoading(false);
      }, 1000);
    } else {
      // Demo registration - just show success and switch to login
      setTimeout(() => {
        if (!fullName) {
          setError('Full name is required');
          setLoading(false);
          return;
        }
        
        if (password !== confirmPassword) {
          setError('Passwords do not match');
          setLoading(false);
          return;
        }
        
        if (!termsAccepted) {
          setError('You must accept the Terms of Service');
          setLoading(false);
          return;
        }

        // Switch to login mode with success message
        setIsLoginMode(true);
        setError('');
        setEmail('');
        setPassword('');
        setFullName('');
        setConfirmPassword('');
        setTermsAccepted(false);
        alert('Account created successfully! Please login with your credentials.');
        setLoading(false);
      }, 1000);
    }
  };
  
  const handleBackToHome = () => {
    setShowLogin(false);
  };

  if (showLogin) {
    return (
      <Box sx={{ 
        backgroundColor: '#0e1c40', 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        py: 4,
        backgroundImage: 'linear-gradient(135deg, #0e1c40 0%, #192e5b 100%)',
        backgroundSize: 'cover',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z" fill="%233a5998" fill-opacity="0.1" fill-rule="evenodd"/%3E%3C/svg%3E")',
      }
    }}>
      <Container maxWidth="sm">
        <LoginCard>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="h4" sx={{ 
              color: '#0e1c40', 
              fontWeight: 700, 
              mb: 1,
              position: 'relative',
              display: 'inline-block',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: '-8px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '40px',
                height: '3px',
                background: 'linear-gradient(90deg, #0e1c40, #3a5998)',
                borderRadius: '2px',
              }
            }}>
              StratoSys Report
            </Typography>
            <Typography variant="subtitle1" sx={{ color: '#64748b', mt: 3 }}>
              {isLoginMode ? 'Login to your account' : 'Create a new account'}
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {!isLoginMode && (
            <Alert severity="info" sx={{ mb: 3 }}>
              This is a demo. Any registration information entered will not be stored.
            </Alert>
          )}

          {isLoginMode && (
            <Alert severity="info" sx={{ mb: 3 }}>
              Demo login credentials: <strong>{TEST_EMAIL}</strong> / <strong>{TEST_PASSWORD}</strong>
            </Alert>
          )}

          <form onSubmit={handleLoginSubmit}>
            {!isLoginMode && (
              <>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Full Name</Typography>
                <StyledInput
                  fullWidth
                  placeholder="John Doe"
                  variant="outlined"
                  margin="dense"
                  sx={{ mb: 2 }}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <Box component="span" sx={{ color: '#64748b', mr: 1 }}>
                        <i className="fas fa-user"></i>
                      </Box>
                    ),
                  }}
                />
              </>
            )}

            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Email</Typography>
            <StyledInput
              fullWidth
              placeholder="your@email.com"
              variant="outlined"
              margin="dense"
              sx={{ mb: 2 }}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              InputProps={{
                startAdornment: (
                  <Box component="span" sx={{ color: '#64748b', mr: 1 }}>
                    <i className="fas fa-envelope"></i>
                  </Box>
                ),
              }}
            />

            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Password</Typography>
            <StyledInput
              fullWidth
              type="password"
              placeholder="••••••••"
              variant="outlined"
              margin="dense"
              sx={{ mb: 2 }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              InputProps={{
                startAdornment: (
                  <Box component="span" sx={{ color: '#64748b', mr: 1 }}>
                    <i className="fas fa-lock"></i>
                  </Box>
                ),
              }}
            />

            {!isLoginMode && (
              <>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>Confirm Password</Typography>
                <StyledInput
                  fullWidth
                  type="password"
                  placeholder="••••••••"
                  variant="outlined"
                  margin="dense"
                  sx={{ mb: 2 }}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <Box component="span" sx={{ color: '#64748b', mr: 1 }}>
                        <i className="fas fa-lock"></i>
                      </Box>
                    ),
                  }}
                />

                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={
                      <Checkbox 
                        size="small" 
                        checked={termsAccepted}
                        onChange={(e) => setTermsAccepted(e.target.checked)}
                        sx={{ 
                          color: '#64748b',
                          '&.Mui-checked': {
                            color: '#0e1c40',
                          },
                        }} 
                      />
                    }
                    label={<Typography variant="body2" sx={{ color: '#64748b' }}>I agree to the <span style={{ color: '#0e1c40', fontWeight: 500 }}>Terms of Service</span> and <span style={{ color: '#0e1c40', fontWeight: 500 }}>Privacy Policy</span></Typography>}
                  />
                </Box>
              </>
            )}

            {isLoginMode && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <FormControlLabel
                  control={
                    <Checkbox 
                      size="small" 
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      sx={{ 
                        color: '#64748b',
                        '&.Mui-checked': {
                          color: '#0e1c40',
                        },
                      }} 
                    />
                  }
                  label={<Typography variant="body2" sx={{ color: '#64748b' }}>Remember me</Typography>}
                />
                <Typography variant="body2" sx={{ color: '#0e1c40', cursor: 'pointer', fontWeight: 500, '&:hover': { textDecoration: 'underline' } }}>
                  Forgot password?
                </Typography>
              </Box>
            )}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading}
              sx={{
                bgcolor: '#0e1c40',
                py: 1.5,
                mb: 2,
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1rem',
                borderRadius: '10px',
                boxShadow: '0 10px 25px rgba(14, 28, 64, 0.3)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: '-100%',
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                  transition: 'all 0.6s ease',
                },
                '&:hover': { 
                  bgcolor: '#192e5b',
                  transform: 'translateY(-3px)',
                  boxShadow: '0 15px 30px rgba(14, 28, 64, 0.4)',
                  '&::before': {
                    left: '100%',
                  }
                }
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : (isLoginMode ? 'Login' : 'Sign Up')}
            </Button>

            <Box sx={{ display: 'flex', alignItems: 'center', my: 3 }}>
              <Divider sx={{ flexGrow: 1, borderColor: 'rgba(0,0,0,0.1)' }} />
              <Typography variant="body2" sx={{ mx: 2, color: '#64748b' }}>or</Typography>
              <Divider sx={{ flexGrow: 1, borderColor: 'rgba(0,0,0,0.1)' }} />
            </Box>

            <Box sx={{ 
              mb: 2, 
              display: 'flex', 
              gap: 2,
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              <Button 
                variant="outlined" 
                fullWidth
                startIcon={<GoogleIcon />}
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  color: '#64748b',
                  borderColor: 'rgba(0,0,0,0.1)',
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.2,
                  borderRadius: '10px',
                  '&:hover': {
                    borderColor: '#3a5998',
                    backgroundColor: 'rgba(58, 89, 152, 0.04)',
                  }
                }}
              >
                Google
              </Button>
              
              <Button 
                variant="outlined" 
                fullWidth
                startIcon={<MicrosoftIcon />}
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  color: '#64748b',
                  borderColor: 'rgba(0,0,0,0.1)',
                  textTransform: 'none',
                  fontWeight: 500,
                  py: 1.2,
                  borderRadius: '10px',
                  '&:hover': {
                    borderColor: '#3a5998',
                    backgroundColor: 'rgba(58, 89, 152, 0.04)',
                  }
                }}
              >
                Microsoft
              </Button>
            </Box>

            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography variant="body2" color="textSecondary">
                {isLoginMode ? (
                  <>
                    Don't have an account? <span 
                      style={{ color: '#0e1c40', fontWeight: 600, cursor: 'pointer' }}
                      onClick={() => setIsLoginMode(false)}
                    >
                      Create an account
                    </span>
                  </>
                ) : (
                  <>
                    Already have an account? <span 
                      style={{ color: '#0e1c40', fontWeight: 600, cursor: 'pointer' }}
                      onClick={() => setIsLoginMode(true)}
                    >
                      Login here
                    </span>
                  </>
                )}
              </Typography>
            </Box>

            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#64748b', 
                  cursor: 'pointer', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    color: '#0e1c40',
                  }
                }}
                onClick={handleBackToHome}
              >
                <i className="fas fa-arrow-left" style={{ marginRight: '8px', fontSize: '12px' }}></i>
                Back to Homepage
              </Typography>
            </Box>
          </form>
        </LoginCard>
      </Container>
    </Box>
  );

  return (
    <Box>
      {/* Navigation */}
      <StyledAppBar>
        <StyledToolbar>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography
              variant="h5"
              component="div"
              sx={{
                color: '#0e1c40',
                fontWeight: 700,
                mr: 2,
                display: 'flex',
                alignItems: 'center',
                letterSpacing: '-0.5px',
              }}
            >
              <Box 
                component="span" 
                sx={{ 
                  width: '6px', 
                  height: '1.8rem', 
                  background: 'linear-gradient(180deg, #0e1c40 0%, #3a5998 100%)',
                  display: 'inline-block', 
                  mr: 1.5,
                  borderRadius: '4px',
                }} 
              />
              <span style={{ marginRight: '4px' }}>Strato</span>
              <span style={{ color: '#3a5998' }}>Sys</span>
            </Typography>
          </Box>

          {!isMobile && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <NavButton>About us</NavButton>
              <NavButton>Projects</NavButton>
              <NavButton>Enquiries</NavButton>
              <NavButton>Service</NavButton>
            </Box>
          )}

          <Box>
            <Button
              variant="outlined"
              sx={{
                borderColor: '#3a5998',
                color: '#0e1c40',
                marginRight: 2,
                textTransform: 'none',
                fontWeight: 500,
                borderRadius: '8px',
                px: 3,
                transition: 'all 0.3s ease',
                '&:hover': { 
                  borderColor: '#0e1c40', 
                  color: '#0e1c40',
                  backgroundColor: 'rgba(14, 28, 64, 0.04)', 
                  transform: 'translateY(-3px)',
                },
              }}
              onClick={handleLogin}
            >
              Login
            </Button>
            <RegisterButton variant="contained" onClick={handleRegister}>
              Get Started
            </RegisterButton>
          </Box>
        </StyledToolbar>
      </StyledAppBar>

      {/* About Section */}
      <HeroSection>
        <Container>
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography 
              variant="h1" 
              sx={{ 
                fontWeight: 800, 
                fontSize: { xs: '2.5rem', md: '3.5rem' },
                background: 'linear-gradient(90deg, #0e1c40 0%, #3a5998 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2,
                letterSpacing: '-1px'
              }}
            >
              Transform Report Generation
            </Typography>
            <Typography 
              variant="h5" 
              sx={{ 
                color: '#64748b', 
                fontWeight: 400, 
                maxWidth: '800px',
                mx: 'auto',
                lineHeight: 1.6
              }}
            >
              Streamline your workflow with our powerful, AI-powered report automation system
            </Typography>
            <Box sx={{ mt: 5, display: 'flex', justifyContent: 'center', gap: 3 }}>
              <Button 
                variant="contained" 
                size="large"
                sx={{
                  bgcolor: '#0e1c40',
                  px: 4,
                  py: 1.5,
                  fontSize: '1rem',
                  borderRadius: '8px',
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: '0 10px 25px rgba(14, 28, 64, 0.3)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    bgcolor: '#192e5b',
                    transform: 'translateY(-5px)',
                    boxShadow: '0 15px 30px rgba(14, 28, 64, 0.4)',
                  }
                }}
                onClick={handleRegister}
              >
                Get Started Free
              </Button>
              <Button 
                variant="outlined" 
                size="large"
                sx={{
                  color: '#0e1c40',
                  borderColor: '#3a5998',
                  px: 4,
                  py: 1.5,
                  fontSize: '1rem',
                  borderRadius: '8px',
                  textTransform: 'none',
                  fontWeight: 600,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    borderColor: '#0e1c40',
                    bgcolor: 'rgba(14, 28, 64, 0.04)',
                    transform: 'translateY(-5px)',
                  }
                }}
              >
                <Box component="span" sx={{ mr: 1 }}>
                  <i className="fas fa-play" style={{ fontSize: '12px' }} />
                </Box>
                Watch Demo
              </Button>
            </Box>
          </Box>

          <Box sx={{ mt: 8 }}>
            <Grid container spacing={5} alignItems="center">
              <Grid item xs={12} md={6}>
                <Box sx={{ textAlign: { xs: 'center', md: 'left' }, pb: 4 }}>
                  <Box 
                    sx={{ 
                      display: 'inline-block', 
                      bgcolor: 'rgba(14, 28, 64, 0.08)', 
                      px: 2, 
                      py: 0.7, 
                      borderRadius: '50px',
                      mb: 2
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ color: '#0e1c40', fontWeight: 600 }}>
                      Our Mission
                    </Typography>
                  </Box>
                  <Typography variant="h3" sx={{ color: '#0e1c40', fontWeight: 700, mb: 3, lineHeight: 1.3 }}>
                    Revolutionizing how organizations manage reports
                  </Typography>
                  <Typography variant="body1" sx={{ color: '#64748b', mb: 4, lineHeight: 1.8, fontSize: '1.05rem' }}>
                    StratoSys Report was built by Semester 4 Software Engineering students at 
                    UMK as a final year project. Our mission is to transform the way 
                    organizations generate and manage reports by automating the process 
                    from form submission to PDF generation. We specialize in streamlining 
                    complex reporting workflows for educational institutions, government 
                    agencies, and corporate environments.
                  </Typography>

                  <Box sx={{ mt: 5, display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Box 
                        sx={{ 
                          bgcolor: 'rgba(14, 28, 64, 0.08)', 
                          p: 1, 
                          borderRadius: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 48,
                          height: 48
                        }}
                      >
                        <i className="fas fa-check" style={{ color: '#0e1c40', fontSize: '1.2rem' }} />
                      </Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        Automated report generation in seconds
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Box 
                        sx={{ 
                          bgcolor: 'rgba(14, 28, 64, 0.08)', 
                          p: 1, 
                          borderRadius: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 48,
                          height: 48
                        }}
                      >
                        <i className="fas fa-check" style={{ color: '#0e1c40', fontSize: '1.2rem' }} />
                      </Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        Secure integration with existing systems
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Box 
                        sx={{ 
                          bgcolor: 'rgba(14, 28, 64, 0.08)', 
                          p: 1, 
                          borderRadius: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 48,
                          height: 48
                        }}
                      >
                        <i className="fas fa-check" style={{ color: '#0e1c40', fontSize: '1.2rem' }} />
                      </Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        Customizable templates and branding
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box 
                  sx={{ 
                    position: 'relative',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: '-10px',
                      left: '-10px',
                      width: '100%',
                      height: '100%',
                      borderRadius: '24px',
                      background: 'rgba(58, 89, 152, 0.1)',
                      zIndex: -1,
                    }
                  }}
                >
                  <Box
                    component="img"
                    src="https://i.imgur.com/JR0Z9tA.png" 
                    alt="Report Automation"
                    sx={{ 
                      width: '100%',
                      height: 'auto',
                      borderRadius: '20px',
                      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15)',
                      transform: 'perspective(1500px) rotateY(-5deg)',
                      transition: 'all 0.5s ease',
                      '&:hover': {
                        transform: 'perspective(1500px) rotateY(0deg)',
                      }
                    }}
                  />
                </Box>
              </Grid>
            </Grid>
          </Box>
          
          <Box sx={{ mt: 12 }}>
            <Typography variant="h4" sx={{ textAlign: 'center', fontWeight: 700, mb: 6, color: '#0e1c40' }}>
              Key Features That Set Us Apart
            </Typography>
            <Grid container spacing={4}>
              <Grid item xs={12} md={4}>
                <FeatureCard>
                  <AnimatedIcon>
                    <i className="fas fa-bolt" />
                  </AnimatedIcon>
                  <Typography variant="h6" sx={{ color: '#0e1c40', fontWeight: 700, mb: 1.5 }}>
                    Fast & Efficient
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', lineHeight: 1.7, flex: 1 }}>
                    Generate complex reports in seconds, not days. Our advanced processing engine handles even the most demanding data requirements.
                  </Typography>
                </FeatureCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <FeatureCard>
                  <AnimatedIcon>
                    <i className="fas fa-lock" />
                  </AnimatedIcon>
                  <Typography variant="h6" sx={{ color: '#0e1c40', fontWeight: 700, mb: 1.5 }}>
                    Secure & Private
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', lineHeight: 1.7, flex: 1 }}>
                    Enterprise-grade security with advanced data protection measures ensures your sensitive information remains confidential.
                  </Typography>
                </FeatureCard>
              </Grid>
              <Grid item xs={12} md={4}>
                <FeatureCard>
                  <AnimatedIcon>
                    <i className="fas fa-plug" />
                  </AnimatedIcon>
                  <Typography variant="h6" sx={{ color: '#0e1c40', fontWeight: 700, mb: 1.5 }}>
                    Easily Integrated
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', lineHeight: 1.7, flex: 1 }}>
                    Seamlessly connects with your existing tools and systems including Google Workspace, Microsoft Office, and many more.
                  </Typography>
                </FeatureCard>
              </Grid>
            </Grid>
          </Box>
        </Container>
      </HeroSection>

      {/* Projects Section */}
      <Box sx={{ 
        py: 10,
        background: 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%239C92AC" fill-opacity="0.03"%3E%3Cpath d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }
      }}>
        <Container>
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Box sx={{ 
              display: 'inline-block', 
              bgcolor: 'rgba(14, 28, 64, 0.08)', 
              px: 2.5, 
              py: 0.7, 
              borderRadius: '50px',
              mb: 2 
            }}>
              <Typography variant="subtitle2" sx={{ color: '#0e1c40', fontWeight: 600 }}>
                Our Services
              </Typography>
            </Box>
            <Typography 
              variant="h3" 
              sx={{ 
                color: '#0e1c40', 
                fontWeight: 700, 
                mb: 2,
                background: 'linear-gradient(90deg, #0e1c40 30%, #3a5998 70%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Comprehensive Reporting Solutions
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                color: '#64748b', 
                maxWidth: '700px', 
                mx: 'auto', 
                lineHeight: 1.8,
                mb: 3,
              }}
            >
              Discover our suite of powerful tools designed to streamline your reporting workflow
              and transform how you manage information in your organization.
            </Typography>
          </Box>
          
          <Grid container spacing={4} sx={{ mt: 4 }}>
            <Grid item xs={12} sm={6} md={4}>
              <ProjectCard>
                <AnimatedProjectImage>
                  <img 
                    src="https://i.imgur.com/HnWMUMN.png" 
                    alt="Report Generator" 
                    className="project-image"
                  />
                </AnimatedProjectImage>
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#0e1c40' }}>
                    StratoSys Report Generator
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', mb: 3, lineHeight: 1.7 }}>
                    Automated report generation system that converts form submissions into 
                    professional PDF reports with customizable templates and branding.
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 3 }}>
                    <ProjectTag label="React.js" />
                    <ProjectTag label="PDF Generation" />
                    <ProjectTag label="Google API" />
                  </Box>
                  <ViewProjectButton variant="contained" sx={{ alignSelf: 'center' }}>
                    <i className="fas fa-arrow-right" style={{ marginRight: 8, fontSize: 12 }} />
                    View Project
                  </ViewProjectButton>
                </CardContent>
              </ProjectCard>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <ProjectCard>
                <AnimatedProjectImage>
                  <img 
                    src="https://i.imgur.com/JZBi7l7.png" 
                    alt="Google Workspace Integration"
                    className="project-image"
                  />
                </AnimatedProjectImage>
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#0e1c40' }}>
                    Google Workspace Integration
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', mb: 3, lineHeight: 1.7 }}>
                    Seamless integration with Google Forms, Sheets, and Drive for efficient
                    data collection, processing, and secure cloud storage.
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 3 }}>
                    <ProjectTag label="Google API" />
                    <ProjectTag label="OAuth 2.0" />
                    <ProjectTag label="Data Sync" />
                  </Box>
                  <ViewProjectButton variant="contained" sx={{ alignSelf: 'center' }}>
                    <i className="fas fa-arrow-right" style={{ marginRight: 8, fontSize: 12 }} />
                    View Project
                  </ViewProjectButton>
                </CardContent>
              </ProjectCard>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <ProjectCard>
                <AnimatedProjectImage>
                  <img 
                    src="https://i.imgur.com/JR0Z9tA.png" 
                    alt="Analytics Dashboard"
                    className="project-image"
                  />
                </AnimatedProjectImage>
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#0e1c40' }}>
                    Real-Time Analytics Dashboard
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', mb: 3, lineHeight: 1.7 }}>
                    Live data visualization and analytics dashboard for monitoring report 
                    generation metrics and user engagement patterns.
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 3 }}>
                    <ProjectTag label="Chart.js" />
                    <ProjectTag label="Real-time Data" />
                    <ProjectTag label="Socket.io" />
                  </Box>
                  <ViewProjectButton variant="contained" sx={{ alignSelf: 'center' }}>
                    <i className="fas fa-arrow-right" style={{ marginRight: 8, fontSize: 12 }} />
                    View Project
                  </ViewProjectButton>
                </CardContent>
              </ProjectCard>
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
                  Projects
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                  Enquiries
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ cursor: 'pointer' }}>
                  Service
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
    </Box>
  );
}

}

export default LandingPage;
