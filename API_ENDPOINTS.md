# Backend API Endpoints Summary

Last Updated: November 14, 2025
Authentication: Firebase ID Token (Bearer header)

## AUTHENTICATION ROUTES
- POST /auth/firebase-sync - Login/sync Firebase user (30/min rate limit)
- POST /auth/verify-token - Verify Firebase token
- POST /auth/logout - Logout user
- GET /auth/profile - Get user profile
- PUT /auth/profile - Update user profile
- GET /auth/firebase-health - Firebase health check
- GET /auth/firebase-config-validation - Config validation
- POST /auth/firebase-reinitialize - Reinitialize Firebase
- GET /auth/firebase-circuit-breaker - Circuit breaker status
- POST /auth/firebase-circuit-breaker/reset - Reset circuit breaker
- GET /auth/firebase-initialization-history - Initialization history

## REPORT MANAGEMENT
- GET /reports - Get all reports (100/hour rate limit)
- GET /reports/<id> - Get specific report (200/hour rate limit)
- POST /reports - Create report (20/hour rate limit)
- PUT /reports/<id> - Update report (50/hour rate limit)
- DELETE /reports/<id> - Delete report (30/hour rate limit)
- GET /reports/recent - Get recent reports
- GET /reports/history - Get reports history with pagination
- GET /reports/stats - Get report statistics
- GET /reports/templates - Get available templates
- GET /reports/<task_id>/status - Get async task status
- GET /reports/export/pdf/<report_id> - Export as PDF
- POST /reports/<id>/ai-suggestions - Get AI suggestions
- POST /reports/<id>/enhance - Enhance with AI
- POST /reports/<id>/download - Download report (PDF/DOCX/XLSX)
- GET /automated-reports - Get automated reports

## FORMS MANAGEMENT
- GET /api/forms or /admin/forms - Get all forms
- GET /api/forms/<id> or /admin/forms/<id> - Get specific form
- POST /api/forms or /admin/forms - Create form
- PUT /api/forms/<id> or /admin/forms/<id> - Update form
- DELETE /api/forms/<id> or /admin/forms/<id> - Delete form
- PATCH /admin/forms/<id>/toggle/<field> - Toggle form field
- GET /admin/forms/stats - Get form statistics

## GOOGLE FORMS INTEGRATION
- GET /api/google-forms/status - Service status
- GET /api/google-forms/auth - Start OAuth flow
- GET /api/google-forms/callback - OAuth callback (query: code)
- GET /api/google-forms/forms - List user's Google Forms
- GET /api/google-forms/<form_id>/responses - Get form responses
- GET /api/google-forms/<form_id>/analytics - Get form analytics
- GET /api/production/forms/google/list - Production: List forms
- GET /api/production/forms/google/<form_id>/responses - Production: Get responses

## USER MANAGEMENT
- GET /users/profile - Get profile
- PUT /users/profile - Update profile
- POST /users/change-password - Change password
- GET /users/settings - Get settings
- PUT /users/settings - Update settings
- GET /users - List users (Admin, requires view_users permission)
- PUT /users/<id>/role - Update user role (Admin, requires manage_users)
- PUT /users/<id>/status - Update user active status (Admin, requires manage_users)

## ANALYTICS & DASHBOARD
- GET /analytics/dashboard/stats - Dashboard statistics
- GET /analytics/trends - Submission trends
- GET /analytics/top-forms - Top performing forms
- GET /analytics/field-analytics/<form_id> - Field analytics
- GET /analytics/geographic - Geographic distribution
- GET /analytics/time-of-day - Time of day analytics
- GET /analytics/performance-comparison - Performance comparison
- GET /analytics/real-time - Real-time analytics
- GET /analytics/charts/<chart_type> - Chart data

## EXCEL & EXPORT OPERATIONS
- POST /api/ai-excel/generate - Generate Excel from prompt
- GET /api/ai-excel/download/<filename> - Download generated Excel
- POST /api/ai-excel/generate-from-form/<form_id> - Generate from form
- GET /api/ai-excel/health - Excel service health

## ENHANCED REPORTS & VERSIONING
- PUT /reports/<id>/edit - Update and create version
- GET /reports/<id>/versions - Get all versions
- GET /reports/<id>/versions/<version_id> - Get specific version
- POST /reports/<id>/versions/<version_id>/rollback - Rollback version
- GET /reports/<id>/versions/compare/<v1_id>/<v2_id> - Compare versions
- GET /reports/<id>/edit-history - Get edit history
- POST /reports/<id>/auto-save - Auto-save report
- GET /reports/templates - Get templates
- POST /reports/templates - Create template
- POST /reports/<id>/apply-template - Apply template

## CSRF PROTECTION
- GET /csrf/token - Get CSRF token
- POST /csrf/validate - Validate CSRF token
- POST /csrf/refresh - Refresh CSRF token

## HEALTH & STATUS CHECKS
- GET /api/test - API health check
- GET /db-health/health - Database health
- GET /db-health/info - Database connection info
- GET /db-health/status - Database detailed status
- POST /db-health/test - Test database connection
- GET /api/production/health - Production health

## RATE LIMITS
- Firebase Sync: 30/minute
- Reports GET: 100/hour
- Reports GET Detail: 200/hour
- Reports POST: 20/hour
- Reports PUT: 50/hour
- Reports DELETE: 30/hour
- AI Analysis: 10/hour

## PUBLIC ENDPOINTS (No Authentication Required)
- GET /api/test
- GET /db-health/*
- GET /csrf/token
- POST /csrf/validate
- POST /csrf/refresh
- GET /auth/firebase-health
- GET /auth/firebase-config-validation
- GET /api/ai-excel/health
- GET /api/production/health

## RESPONSE CODES
- 200: OK (GET, PUT, DELETE)
- 201: Created (POST)
- 202: Accepted (Async processing)
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error
- 503: Service Unavailable

