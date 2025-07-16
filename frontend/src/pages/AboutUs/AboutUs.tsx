import React from 'react';
import { Box, Container, Typography, Grid, Card, CardContent, Button, Avatar } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function AboutUs() {
  const navigate = useNavigate();
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f8fafc', py: 8 }}>
      <Container maxWidth="md">
        <Typography variant="h2" sx={{ fontWeight: 700, color: '#0e1c40', mb: 2, textAlign: 'center' }}>
          About StratoSys
        </Typography>
        <Typography variant="h5" sx={{ color: '#64748b', mb: 4, textAlign: 'center', fontWeight: 400 }}>
          Transforming enterprise reporting with AI, automation, and modern UX.
        </Typography>
        <Card sx={{ mb: 6, borderRadius: 3, boxShadow: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#0e1c40', fontWeight: 600, mb: 1 }}>
              Our Mission
            </Typography>
            <Typography sx={{ color: '#64748b', mb: 2 }}>
              Empower organizations to make data-driven decisions with confidence and ease by automating and modernizing the reporting process.
            </Typography>
            <Typography variant="h6" sx={{ color: '#0e1c40', fontWeight: 600, mb: 1 }}>
              Our Vision
            </Typography>
            <Typography sx={{ color: '#64748b' }}>
              To be the global leader in secure, scalable, and user-friendly reporting solutions powered by AI and seamless integrations.
            </Typography>
          </CardContent>
        </Card>
        <Typography variant="h4" sx={{ color: '#0e1c40', fontWeight: 700, mb: 3, textAlign: 'center' }}>
          Why Choose StratoSys?
        </Typography>
        <Grid container spacing={4} sx={{ mb: 6 }}>
          <Grid item xs={12} md={3}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#0e1c40', mx: 'auto', mb: 1 }}><i className="fas fa-brain" /></Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>AI-Powered</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>Leverage advanced AI for smart analysis and automation.</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#0e1c40', mx: 'auto', mb: 1 }}><i className="fas fa-lock" /></Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Secure</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>Enterprise-grade security and compliance for your data.</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#0e1c40', mx: 'auto', mb: 1 }}><i className="fas fa-expand-arrows-alt" /></Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Scalable</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>Built to grow with your organization, from startup to enterprise.</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#0e1c40', mx: 'auto', mb: 1 }}><i className="fas fa-user-check" /></Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>User-Friendly</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>Modern, intuitive UI for a delightful user experience.</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        <Typography variant="h4" sx={{ color: '#0e1c40', fontWeight: 700, mb: 3, textAlign: 'center' }}>
          Our Team
        </Typography>
        <Grid container spacing={4} sx={{ mb: 6, justifyContent: 'center' }}>
          <Grid item xs={12} md={4}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#64748b', mx: 'auto', width: 56, height: 56, fontSize: 32 }}>A</Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 1 }}>Alex Tan</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>Founder & CEO</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3 }}>
              <CardContent>
                <Avatar sx={{ bgcolor: '#64748b', mx: 'auto', width: 56, height: 56, fontSize: 32 }}>S</Avatar>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 1 }}>Sarah Lee</Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>CTO</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        <Typography variant="h4" sx={{ color: '#0e1c40', fontWeight: 700, mb: 3, textAlign: 'center' }}>
          Contact Us
        </Typography>
        <Card sx={{ borderRadius: 2, boxShadow: 1, textAlign: 'center', py: 3, mb: 4 }}>
          <CardContent>
            <Typography variant="body1" sx={{ color: '#64748b', mb: 1 }}>
              Email: contact@stratosys.com
            </Typography>
            <Typography variant="body1" sx={{ color: '#64748b' }}>
              Phone: +60 12-345-6789
            </Typography>
          </CardContent>
        </Card>
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Button variant="contained" color="primary" sx={{ px: 4, py: 1.5, fontWeight: 600, borderRadius: 2 }} onClick={() => navigate('/')}>Back to Home</Button>
        </Box>
      </Container>
    </Box>
  );
} 