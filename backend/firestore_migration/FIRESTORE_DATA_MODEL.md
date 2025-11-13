# Firebase Firestore Data Model Design
## Complete Migration from SQL to NoSQL

---

## Design Principles

1. **Denormalization for Read Performance** - Duplicate data where queries are frequent
2. **Flat Structure** - Avoid deep nesting (max 2 levels)
3. **Query Optimization** - Design collections based on access patterns
4. **Composite Indexes** - Define for complex queries
5. **Security-First** - Role-based access control at collection level
6. **Scalability** - Support for real-time updates and high throughput

---

## Collection Structure Overview

```
firestore/
├── users/                              # Top-level collection
│   ├── {userId}/                      # Document
│   │   ├── tokens/                    # Subcollection
│   │   │   └── {platform}/           # Document (google, microsoft)
│   │   ├── sessions/                  # Subcollection
│   │   │   └── {sessionId}/          # Document
│   │   └── quickAccessTokens/         # Subcollection
│   │       └── {tokenId}/            # Document
│
├── forms/                              # Top-level collection
│   ├── {formId}/                      # Document
│   │   ├── submissions/               # Subcollection
│   │   │   └── {submissionId}/       # Document
│   │   ├── qrCodes/                   # Subcollection
│   │   │   └── {qrCodeId}/           # Document
│   │   └── accessCodes/               # Subcollection
│   │       └── {codeId}/             # Document
│
├── programs/                           # Top-level collection
│   ├── {programId}/                   # Document
│   │   ├── participants/              # Subcollection
│   │   │   └── {participantId}/      # Document
│   │   │       └── attendance/        # Subcollection
│   │   │           └── {recordId}/   # Document
│   │   └── integrations/              # Subcollection
│   │       └── {integrationId}/      # Document
│   │           └── responses/         # Subcollection
│   │               └── {responseId}/ # Document
│
├── reports/                            # Top-level collection
│   ├── {reportId}/                    # Document
│   │   └── analytics/                 # Subcollection
│   │       └── {analyticsId}/        # Document
│
├── reportTemplates/                    # Top-level collection
│   └── {templateId}/                  # Document
│
├── files/                              # Top-level collection
│   └── {fileId}/                      # Document
│
├── apiIntegrations/                    # Top-level collection
│   ├── {integrationId}/               # Document
│   │   ├── metrics/                   # Subcollection
│   │   │   └── {metricId}/           # Document
│   │   └── auditLog/                  # Subcollection
│   │       └── {logId}/              # Document
│
└── systemMetrics/                      # Top-level collection (for analytics)
    ├── dailyStats/                    # Document with date as ID
    ├── userActivity/                  # Document
    └── formAnalytics/                 # Document
```

---

## Detailed Collection Schemas

### 1. USERS Collection

**Collection Path**: `/users/{userId}`

**Document Structure**:
```javascript
{
  // Core Identity
  userId: "string",                    // Auto-generated or Firebase UID
  firebaseUid: "string",              // Firebase Auth UID
  email: "string",                     // Indexed
  username: "string",                  // Indexed, unique
  passwordHash: "string",              // If using custom auth

  // Profile Information
  profile: {
    firstName: "string",
    lastName: "string",
    phone: "string",
    company: "string",
    jobTitle: "string",
    bio: "string",
    avatarUrl: "string"
  },

  // Account Status
  isActive: boolean,
  role: "string",                      // "admin", "user", "moderator"

  // Timestamps
  createdAt: timestamp,
  updatedAt: timestamp,
  lastLogin: timestamp,

  // Denormalized Counts (for quick access)
  stats: {
    formsCreated: number,
    formsSubmitted: number,
    programsAttended: number,
    reportsGenerated: number,
    totalSessions: number,
    activeOAuthConnections: number
  },

  // Search Optimization
  searchTerms: ["string"],            // Lowercase tokens for search

  // Indexes needed
  _indexes: {
    email: "string",
    username: "string",
    role: "string",
    isActive: boolean
  }
}
```

#### Subcollection: `/users/{userId}/tokens/{platform}`

```javascript
{
  platform: "string",                  // "google" | "microsoft"
  platformUserId: "string",
  accessToken: "string",               // Encrypted
  refreshToken: "string",              // Encrypted
  tokenType: "string",
  scopes: ["string"],
  expiresAt: timestamp,
  issuedAt: timestamp,
  isActive: boolean,
  lastUsed: timestamp,
  usageCount: number,
  revokedAt: timestamp | null,
  revokeReason: "string" | null
}
```

#### Subcollection: `/users/{userId}/sessions/{sessionId}`

```javascript
{
  sessionId: "string",
  sessionToken: "string",              // Indexed
  ipAddress: "string",
  userAgent: "string",
  browser: "string",
  operatingSystem: "string",
  deviceType: "string",                // "mobile", "desktop", "tablet"
  loginMethod: "string",               // "password", "google", "microsoft"

  isActive: boolean,
  isSuspicious: boolean,
  securityFlags: {
    newDevice: boolean,
    newLocation: boolean,
    unusualTime: boolean
  },

  createdAt: timestamp,
  lastActivity: timestamp,
  expiresAt: timestamp,
  endedAt: timestamp | null
}
```

#### Subcollection: `/users/{userId}/quickAccessTokens/{tokenId}`

```javascript
{
  token: "string",                     // Indexed
  email: "string",
  phone: "string",
  name: "string",
  accessType: "string",

  // OTP Verification
  otpCode: "string",
  otpExpiresAt: timestamp,
  otpVerified: boolean,

  // Usage Tracking
  isActive: boolean,
  expiresAt: timestamp,
  maxUses: number | null,
  currentUses: number,

  allowedForms: ["formId"],            // Array of form IDs

  createdAt: timestamp,
  lastUsed: timestamp,
  ipAddress: "string",
  userAgent: "string"
}
```

---

### 2. FORMS Collection

**Collection Path**: `/forms/{formId}`

**Document Structure**:
```javascript
{
  formId: "string",                    // Auto-generated

  // Basic Information
  title: "string",
  description: "string",
  schema: {                            // JSON Schema for form fields
    fields: [
      {
        fieldId: "string",
        fieldType: "string",           // text, number, select, etc.
        label: "string",
        required: boolean,
        options: ["string"] | null,
        validation: {}
      }
    ]
  },

  // Access Control
  isActive: boolean,
  isPublic: boolean,
  accessKey: "string",

  // Owner Information (Denormalized)
  creator: {
    userId: "string",
    username: "string",
    email: "string"
  },

  // Form Settings
  settings: {
    allowAnonymous: boolean,
    requireLogin: boolean,
    enableNotifications: boolean,
    successMessage: "string",
    redirectUrl: "string"
  },

  // Limitations
  submissionLimit: number | null,
  expiresAt: timestamp | null,

  // URLs and Sharing
  externalUrl: "string",
  qrCodeData: "string",                // Base64

  // Analytics (Denormalized for quick access)
  stats: {
    viewCount: number,
    submissionCount: number,
    uniqueSubmitters: number,
    averageCompletionTime: number,
    lastSubmissionAt: timestamp | null
  },

  // Timestamps
  createdAt: timestamp,
  updatedAt: timestamp,

  // Search Optimization
  searchTerms: ["string"],

  // Indexes
  _indexes: {
    creatorId: "string",
    isActive: boolean,
    isPublic: boolean,
    createdAt: timestamp
  }
}
```

#### Subcollection: `/forms/{formId}/submissions/{submissionId}`

```javascript
{
  submissionId: "string",

  // Submission Data
  data: {                              // Dynamic based on form schema
    [fieldId]: "any"
  },

  // Submitter Information (Denormalized)
  submitter: {
    userId: "string" | null,
    email: "string",
    username: "string" | null,
    firstName: "string" | null,
    lastName: "string" | null
  },

  // Submission Context
  submittedAt: timestamp,
  status: "string",                    // "submitted", "processing", "processed", "failed"
  submissionSource: "string",          // "web", "mobile", "qr", "api"

  // Technical Details
  ipAddress: "string",
  userAgent: "string",
  locationData: {
    country: "string",
    city: "string",
    coordinates: geopoint | null
  },

  // Processing
  processingNotes: "string",
  processedAt: timestamp | null,

  // Indexes
  _indexes: {
    submitterUserId: "string",
    submittedAt: timestamp,
    status: "string"
  }
}
```

#### Subcollection: `/forms/{formId}/qrCodes/{qrCodeId}`

```javascript
{
  qrCodeId: "string",
  qrCodeData: "string",                // Base64
  externalUrl: "string",

  title: "string",
  description: "string",

  // QR Code Settings
  size: number,
  errorCorrection: "string",           // "L", "M", "Q", "H"
  border: number,
  backgroundColor: "string",
  foregroundColor: "string",

  // Analytics
  scanCount: number,
  lastScanned: timestamp | null,

  isActive: boolean,
  createdAt: timestamp,
  updatedAt: timestamp
}
```

#### Subcollection: `/forms/{formId}/accessCodes/{codeId}`

```javascript
{
  codeId: "string",
  accessCode: "string",                // Indexed, unique
  description: "string",

  isActive: boolean,
  expiresAt: timestamp | null,

  maxUses: number | null,
  currentUses: number,

  createdAt: timestamp,

  // Usage Tracking
  usageHistory: [
    {
      usedAt: timestamp,
      userId: "string",
      ipAddress: "string"
    }
  ]
}
```

---

### 3. PROGRAMS Collection

**Collection Path**: `/programs/{programId}`

**Document Structure**:
```javascript
{
  programId: "string",
  uuid: "string",                      // For external references

  // Program Details
  title: "string",
  description: "string",

  // Schedule
  startDate: timestamp,
  endDate: timestamp,

  // People
  location: "string",
  organizer: "string",
  speaker: "string",
  trainer: "string",
  facilitator: "string",

  // Program Content
  background: "string",
  objectives: "string",
  requirements: "string",

  // Capacity
  capacity: number,
  status: "string",                    // "draft", "active", "completed", "cancelled"

  // Form Integration
  formSource: "string",                // "internal", "google_forms", "microsoft_forms"
  formId: "string" | null,

  // Denormalized Stats
  stats: {
    totalParticipants: number,
    attendedParticipants: number,
    averageAttendance: number,
    totalSessions: number,
    completionRate: number
  },

  // Timestamps
  createdAt: timestamp,
  updatedAt: timestamp,

  // Search
  searchTerms: ["string"],

  // Indexes
  _indexes: {
    status: "string",
    startDate: timestamp,
    endDate: timestamp
  }
}
```

#### Subcollection: `/programs/{programId}/participants/{participantId}`

```javascript
{
  participantId: "string",

  // Personal Information
  fullName: "string",
  identificationNumber: "string",
  email: "string",
  phone: "string",
  gender: "string",
  age: number,

  // Organization
  organization: "string",
  position: "string",
  department: "string",

  // Registration
  registrationDate: timestamp,
  registrationSource: "string",        // "manual", "form", "import"
  formResponseId: "string" | null,
  status: "string",                    // "registered", "confirmed", "attended", "cancelled"

  // Additional Info
  address: "string",
  emergencyContact: "string",
  dietaryRequirements: "string",
  specialNeeds: "string",

  // Denormalized Attendance Summary
  attendanceSummary: {
    totalDays: number,
    daysAttended: number,
    attendancePercentage: number,
    totalHoursAttended: number,
    status: "string"                   // "excellent", "good", "poor"
  },

  // Indexes
  _indexes: {
    email: "string",
    identificationNumber: "string",
    status: "string"
  }
}
```

#### Subcollection: `/programs/{programId}/participants/{participantId}/attendance/{recordId}`

```javascript
{
  recordId: "string",

  // Multi-day Attendance Tracking
  attendance: {
    day1: {
      status: "string",                // "present", "absent", "late", "excused"
      checkInTime: timestamp | null,
      checkOutTime: timestamp | null,
      hoursAttended: number
    },
    day2: { /* same structure */ },
    day3: { /* same structure */ },
    day4: { /* same structure */ },
    day5: { /* same structure */ }
  },

  // Summary
  totalHoursAttended: number,
  attendancePercentage: number,

  // Notes
  notes: "string",
  recordedBy: {
    userId: "string",
    username: "string"
  },
  recordedAt: timestamp,

  // Indexes
  _indexes: {
    recordedAt: timestamp
  }
}
```

#### Subcollection: `/programs/{programId}/integrations/{integrationId}`

```javascript
{
  integrationId: "string",

  platform: "string",                  // "google_forms", "microsoft_forms"
  formId: "string",                    // External form ID
  formTitle: "string",
  formUrl: "string",

  // Integration Status
  integrationStatus: "string",         // "active", "paused", "error"
  lastSync: timestamp | null,
  syncCount: number,
  errorMessage: "string" | null,

  // Configuration
  configuration: {
    autoSync: boolean,
    syncFrequency: "string",           // "realtime", "hourly", "daily"
    fieldMapping: {
      [externalFieldId]: "internalFieldName"
    }
  },

  // OAuth Info (Denormalized)
  oAuthUser: {
    userId: "string",
    email: "string",
    platform: "string"
  },

  webhookUrl: "string" | null,

  createdAt: timestamp,
  createdBy: {
    userId: "string",
    username: "string"
  },

  // Stats
  stats: {
    totalResponses: number,
    lastResponseAt: timestamp | null
  }
}
```

#### Subcollection: `/programs/{programId}/integrations/{integrationId}/responses/{responseId}`

```javascript
{
  responseId: "string",
  externalResponseId: "string",        // ID from external platform

  // Raw Data
  responseData: {                      // Original response from external platform
    [key]: "any"
  },

  // Normalized Data
  normalizedData: {                    // Mapped to internal schema
    [fieldName]: "any"
  },

  // Processing
  submittedAt: timestamp,
  processedAt: timestamp | null,
  processingStatus: "string",          // "pending", "processed", "failed", "duplicate"
  processingError: "string" | null,

  // Link to Participant (if processed)
  participantId: "string" | null,

  // Quality Scores
  completionScore: number,             // 0-100
  dataQualityScore: number,            // 0-100

  // Indexes
  _indexes: {
    externalResponseId: "string",
    processingStatus: "string",
    submittedAt: timestamp
  }
}
```

---

### 4. REPORTS Collection

**Collection Path**: `/reports/{reportId}`

**Document Structure**:
```javascript
{
  reportId: "string",

  // Relations
  programId: "string",
  templateId: "string",

  // Report Details
  title: "string",
  description: "string",
  reportType: "string",                // "program_summary", "attendance", "custom"

  // Generation Status
  generationStatus: "string",          // "pending", "processing", "completed", "failed"
  generatedAt: timestamp | null,
  generationTimeSeconds: number,

  // File Information
  filePath: "string",
  fileSize: number,
  fileFormat: "string",                // "docx", "pdf", "xlsx", "html"
  downloadUrl: "string",

  // Download Tracking
  downloadCount: number,
  lastDownloaded: timestamp | null,

  // Data Source
  dataSource: {
    type: "string",                    // "program", "form", "manual"
    sourceId: "string",
    recordCount: number,
    dateRange: {
      from: timestamp,
      to: timestamp
    }
  },

  // Generation Config
  generationConfig: {
    includeCharts: boolean,
    includeImages: boolean,
    language: "string",
    template: "string"
  },

  // Quality Metrics
  completenessScore: number,           // 0-100
  dataQualityScore: number,            // 0-100

  // Error Handling
  errorMessage: "string" | null,
  processingNotes: "string",

  // Creator (Denormalized)
  createdBy: {
    userId: "string",
    username: "string",
    email: "string"
  },
  createdAt: timestamp,

  // Indexes
  _indexes: {
    programId: "string",
    templateId: "string",
    generationStatus: "string",
    createdAt: timestamp
  }
}
```

#### Subcollection: `/reports/{reportId}/analytics/{analyticsId}`

```javascript
{
  analyticsId: "string",

  // Statistical Analysis
  participantStatistics: {
    totalParticipants: number,
    byGender: { male: number, female: number, other: number },
    byAgeGroup: { "18-25": number, "26-35": number, /* etc */ },
    byOrganization: { [orgName]: number }
  },

  attendanceStatistics: {
    overallAttendance: number,
    dailyAttendance: [number],
    averageHours: number,
    perfectAttendance: number
  },

  programEffectiveness: {
    completionRate: number,
    satisfactionScore: number,
    engagementLevel: "string"
  },

  // AI-Generated Insights
  aiInsights: {
    summary: "string",
    strengths: ["string"],
    weaknesses: ["string"],
    trends: ["string"]
  },

  // Response Patterns (from forms)
  responsePatterns: {
    commonAnswers: {},
    outliers: {},
    sentimentAnalysis: {}
  },

  engagementMetrics: {
    activeParticipation: number,
    responseTime: number,
    interactionScore: number
  },

  // Quality & Reliability
  dataQualityScore: number,
  completenessPercentage: number,
  reliabilityScore: number,

  // Key Findings
  keyFindings: [
    {
      title: "string",
      description: "string",
      importance: "string",            // "high", "medium", "low"
      category: "string"
    }
  ],

  // Recommendations
  recommendations: [
    {
      title: "string",
      description: "string",
      priority: "string",
      actionable: boolean
    }
  ],

  // Action Items
  actionItems: [
    {
      task: "string",
      assignee: "string",
      deadline: timestamp,
      status: "string"
    }
  ],

  // Metadata
  analysisDate: timestamp,
  analysisVersion: "string",

  // Indexes
  _indexes: {
    analysisDate: timestamp
  }
}
```

---

### 5. REPORT TEMPLATES Collection

**Collection Path**: `/reportTemplates/{templateId}`

```javascript
{
  templateId: "string",

  name: "string",
  description: "string",
  templateType: "string",              // "docx", "pdf", "excel", "html"
  category: "string",

  // File Reference
  filePath: "string",                  // Storage bucket path
  fileUrl: "string",

  // Placeholder Schema
  placeholderSchema: {
    placeholders: [
      {
        name: "string",
        type: "string",                // "text", "image", "table", "chart"
        required: boolean,
        description: "string"
      }
    ]
  },

  // Capabilities
  supportsCharts: boolean,
  supportsImages: boolean,
  maxParticipants: number | null,

  // Usage Tracking
  usageCount: number,
  lastUsed: timestamp | null,

  // Version Control
  version: "string",
  isActive: boolean,

  // Creator (Denormalized)
  createdBy: {
    userId: "string",
    username: "string"
  },
  createdAt: timestamp,
  updatedAt: timestamp,

  // Indexes
  _indexes: {
    category: "string",
    templateType: "string",
    isActive: boolean
  }
}
```

---

### 6. FILES Collection

**Collection Path**: `/files/{fileId}`

```javascript
{
  fileId: "string",

  // File Information
  filename: "string",
  originalFilename: "string",
  filePath: "string",                  // Storage bucket path
  fileUrl: "string",                   // Download URL
  fileSize: number,
  mimeType: "string",

  // Uploader (Denormalized)
  uploader: {
    userId: "string",
    username: "string",
    email: "string"
  },
  uploadedAt: timestamp,

  // Metadata
  description: "string",
  tags: ["string"],

  // Access Control
  isPublic: boolean,
  isActive: boolean,
  accessKey: "string" | null,

  // Processing Status (for images, videos, etc.)
  processingStatus: "string",          // "pending", "processing", "completed", "failed"
  processingError: "string" | null,
  processedAt: timestamp | null,

  // Download Tracking
  downloadCount: number,
  lastDownloaded: timestamp | null,

  // Indexes
  _indexes: {
    uploaderId: "string",
    isPublic: boolean,
    uploadedAt: timestamp
  }
}
```

---

### 7. API INTEGRATIONS Collection

**Collection Path**: `/apiIntegrations/{integrationId}`

```javascript
{
  integrationId: "string",

  // User Association
  userId: "string",
  userEmail: "string",                 // Denormalized

  // Service Details
  serviceType: "string",               // "google", "microsoft", "other"
  serviceUserId: "string",

  // OAuth Credentials (Encrypted)
  encryptedRefreshToken: "string",

  // Status
  status: "string",                    // "active", "expired", "revoked", "error"
  scopes: ["string"],

  // Sync Information
  lastSyncAt: timestamp | null,
  nextSyncAt: timestamp | null,
  syncFrequency: "string",

  // Timestamps
  createdAt: timestamp,
  updatedAt: timestamp,

  // Stats (Denormalized)
  stats: {
    totalSyncs: number,
    successfulSyncs: number,
    failedSyncs: number,
    lastError: "string" | null
  },

  // Indexes
  _indexes: {
    userId: "string",
    serviceType: "string",
    status: "string"
  }
}
```

#### Subcollection: `/apiIntegrations/{integrationId}/metrics/{metricId}`

```javascript
{
  metricId: "string",
  metricType: "string",                // "sync", "api_call", "data_transfer"
  metricValue: number,
  unit: "string",
  recordedAt: timestamp,

  additionalData: {
    [key]: "any"
  }
}
```

#### Subcollection: `/apiIntegrations/{integrationId}/auditLog/{logId}`

```javascript
{
  logId: "string",

  operation: "string",                 // "sync", "token_refresh", "revoke", etc.
  operationData: {
    [key]: "any"
  },

  success: boolean,
  errorMessage: "string" | null,

  createdAt: timestamp,

  // Context
  ipAddress: "string",
  userAgent: "string"
}
```

---

### 8. SYSTEM METRICS Collection (Aggregated Analytics)

**Collection Path**: `/systemMetrics/dailyStats/{date}`

```javascript
{
  date: "string",                      // "YYYY-MM-DD"

  // User Metrics
  userMetrics: {
    totalUsers: number,
    activeUsers: number,
    newRegistrations: number,
    totalLogins: number,
    uniqueLogins: number
  },

  // Form Metrics
  formMetrics: {
    totalForms: number,
    activeForms: number,
    newForms: number,
    totalSubmissions: number,
    totalViews: number
  },

  // Program Metrics
  programMetrics: {
    totalPrograms: number,
    activePrograms: number,
    totalParticipants: number,
    averageAttendance: number
  },

  // Report Metrics
  reportMetrics: {
    reportsGenerated: number,
    successfulReports: number,
    failedReports: number,
    totalDownloads: number
  },

  // System Performance
  systemPerformance: {
    averageResponseTime: number,
    errorRate: number,
    uptime: number
  },

  calculatedAt: timestamp
}
```

---

## Query Patterns & Composite Indexes

### Required Composite Indexes

```javascript
// 1. Users - Search by role and status
{
  collectionGroup: "users",
  fields: [
    { fieldPath: "role", order: "ASCENDING" },
    { fieldPath: "isActive", order: "ASCENDING" },
    { fieldPath: "createdAt", order: "DESCENDING" }
  ]
}

// 2. Forms - Creator's active forms
{
  collectionGroup: "forms",
  fields: [
    { fieldPath: "creator.userId", order: "ASCENDING" },
    { fieldPath: "isActive", order: "ASCENDING" },
    { fieldPath: "createdAt", order: "DESCENDING" }
  ]
}

// 3. Form Submissions - By form and date
{
  collectionGroup: "submissions",
  fields: [
    { fieldPath: "submittedAt", order: "DESCENDING" }
  ]
}

// 4. Programs - Active programs by date
{
  collectionGroup: "programs",
  fields: [
    { fieldPath: "status", order: "ASCENDING" },
    { fieldPath: "startDate", order: "DESCENDING" }
  ]
}

// 5. Reports - User's reports by status
{
  collectionGroup: "reports",
  fields: [
    { fieldPath: "createdBy.userId", order: "ASCENDING" },
    { fieldPath: "generationStatus", order: "ASCENDING" },
    { fieldPath: "createdAt", order: "DESCENDING" }
  ]
}

// 6. Sessions - Active sessions by user
{
  collectionGroup: "sessions",
  fields: [
    { fieldPath: "isActive", order: "ASCENDING" },
    { fieldPath: "lastActivity", order: "DESCENDING" }
  ]
}
```

---

## Data Migration Strategy

### Phase 1: Initial Setup
1. Create all collections and subcollections
2. Set up composite indexes
3. Configure security rules
4. Test with sample data

### Phase 2: Data Migration
1. Export SQL data to JSON
2. Transform data to Firestore structure
3. Batch write to Firestore (500 docs per batch)
4. Verify data integrity
5. Update denormalized fields

### Phase 3: Application Integration
1. Replace SQL queries with Firestore queries
2. Implement real-time listeners
3. Update API endpoints
4. Test all CRUD operations

### Phase 4: Optimization
1. Monitor query performance
2. Add missing indexes
3. Optimize denormalization strategy
4. Implement caching where needed

---

## Key Differences from SQL

| Aspect | SQL | Firestore |
|--------|-----|-----------|
| **Relationships** | Foreign Keys | Denormalization + References |
| **Joins** | JOIN queries | Multiple reads or denormalization |
| **Transactions** | ACID transactions | Limited transactions (500 docs) |
| **Queries** | Complex WHERE clauses | Limited filters, need indexes |
| **Aggregations** | COUNT, SUM, AVG | Manual aggregation or Cloud Functions |
| **Updates** | UPDATE with WHERE | Update individual documents |
| **Search** | LIKE, FULLTEXT | Need third-party (Algolia) or array-contains |

---

## Best Practices Applied

✅ **Denormalization**: User info duplicated in forms, programs, reports
✅ **Flat Structure**: Max 2-level nesting (collection → document → subcollection)
✅ **Stats Aggregation**: Pre-calculated counts stored in parent documents
✅ **Composite Indexes**: Defined for common query patterns
✅ **Security Rules**: Role-based access at collection level
✅ **Real-time Ready**: Structure supports Firestore real-time listeners
✅ **Scalability**: Collections can grow indefinitely
✅ **Query Optimization**: Indexed fields for fast lookups

---

**Next Steps**:
1. Review this data model
2. Create Firestore security rules
3. Generate migration scripts
4. Implement Firestore query functions
