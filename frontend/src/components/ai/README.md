# AI Components Documentation

This directory contains React components that provide AI-powered functionality for data analysis, report suggestions, and smart placeholders.

## Overview

The AI components integrate with the backend AI service to provide intelligent features while maintaining robust fallback mechanisms when AI services are unavailable.

## Components

### 1. AIHub

**Main entry point component that combines all AI features in a tabbed interface.**

```typescript
import { AIHub } from "./components/ai";

<AIHub
  data={yourData}
  reports={existingReports}
  context="business_intelligence"
  onAnalysisComplete={(result) => console.log(result)}
  onSuggestionApply={(suggestion) => console.log(suggestion)}
  onPlaceholderSelect={(placeholder) => console.log(placeholder)}
/>;
```

**Props:**

- `data?: Record<string, unknown>` - Data to analyze
- `reports?: Record<string, unknown>[]` - Existing reports for suggestions
- `context?: string` - Context for AI operations (default: 'general')
- `onAnalysisComplete?: (result: AIAnalysisResult) => void` - Analysis callback
- `onSuggestionApply?: (suggestion: AIReportSuggestion) => void` - Suggestion callback
- `onPlaceholderSelect?: (placeholder: AIPlaceholder) => void` - Placeholder callback

### 2. AIAnalysisDashboard

**Analyzes data and displays insights, patterns, recommendations, and anomalies.**

```typescript
import { AIAnalysisDashboard } from "./components/ai";

<AIAnalysisDashboard
  data={{
    sales: [{ month: "Jan", revenue: 45000 }],
    expenses: { marketing: 15000 },
  }}
  context="sales_dashboard"
  onAnalysisComplete={(result) => handleAnalysis(result)}
  autoAnalyze={true}
/>;
```

**Features:**

- Data quality assessment
- Key insights and patterns detection
- Recommendations and anomaly identification
- Risk assessment and opportunities
- AI/rule-based analysis with confidence scoring

### 3. AIReportSuggestions

**Generates intelligent report structure and content suggestions.**

```typescript
import { AIReportSuggestions } from './components/ai';

<AIReportSuggestions
  reports={[
    { title: 'Q1 Sales', type: 'sales', data: {...} },
    { title: 'Marketing Performance', type: 'marketing', data: {...} }
  ]}
  context="business_analytics"
  onSuggestionApply={(suggestion) => createReport(suggestion)}
  autoGenerate={false}
/>
```

**Features:**

- Key metrics identification
- Visualization recommendations
- Report structure suggestions (trends, critical areas, executive points)
- Quality scoring and next steps

### 4. AISmartPlaceholders

**Creates contextual placeholders for dynamic content in templates.**

```typescript
import { AISmartPlaceholders } from "./components/ai";

<AISmartPlaceholders
  context="financial_report"
  industry="technology"
  onPlaceholderSelect={(placeholder) => insertPlaceholder(placeholder)}
  autoGenerate={false}
/>;
```

**Features:**

- Context-aware placeholder generation
- Multiple categories (basic, financial, operational, industry-specific)
- Copy-to-clipboard functionality
- Format and example information

## Data Flow

```
Frontend Components → aiService.ts → Backend API → AI Service → Response
                   ← Error Handling ← Fallback Logic ← OpenAI/Rules ←
```

## Error Handling

All components include comprehensive error handling:

1. **Network Errors**: Graceful degradation with user-friendly messages
2. **AI Service Unavailable**: Automatic fallback to rule-based analysis
3. **Invalid Data**: Input validation with helpful error messages
4. **Rate Limiting**: Proper handling of API limits

## Styling

Components use Material-UI (MUI) for consistent styling:

- **Colors**: Primary (blue), secondary (green), error (red), warning (orange)
- **Typography**: Clear hierarchy with proper contrast
- **Layout**: Responsive grid system with proper spacing
- **Icons**: Material Icons for consistent visual language

## TypeScript Interfaces

```typescript
interface AIAnalysisResult {
  success: boolean;
  summary: string;
  insights: string[];
  recommendations: string[];
  patterns: string[];
  anomalies: string[];
  risks: string[];
  opportunities: string[];
  data_quality: "high" | "medium" | "low";
  confidence_score: number;
  analysis_type: string;
  ai_powered: boolean;
  fallback_reason?: string;
  timestamp: string;
  error?: string;
}

interface AIReportSuggestion {
  key_metrics: Array<{
    metric: string;
    value: string;
    importance: "high" | "medium" | "low";
    description: string;
  }>;
  visualizations: Array<{
    type: string;
    data_fields: string[];
    purpose: string;
  }>;
  trends: string[];
  critical_areas: string[];
  executive_points: string[];
  detailed_sections: string[];
  next_steps: string[];
  report_quality_score: number;
}

interface AIPlaceholder {
  name: string;
  description: string;
  example: string;
  required?: boolean;
  format?: string;
  context?: string;
  optional?: boolean;
  dynamic?: boolean;
}
```

## Usage Examples

### Basic Data Analysis

```typescript
const MyComponent = () => {
  const [analysis, setAnalysis] = useState(null);

  const sampleData = {
    sales: [{ month: "Jan", revenue: 45000 }],
    kpis: { conversion_rate: 3.2 },
  };

  return (
    <AIAnalysisDashboard
      data={sampleData}
      context="monthly_report"
      onAnalysisComplete={setAnalysis}
      autoAnalyze={true}
    />
  );
};
```

### Report Suggestions with Custom Handler

```typescript
const ReportBuilder = () => {
  const handleSuggestion = (suggestion: AIReportSuggestion) => {
    // Create new report template based on suggestion
    const template = {
      metrics: suggestion.key_metrics,
      charts: suggestion.visualizations,
      sections: suggestion.detailed_sections,
    };
    createReportTemplate(template);
  };

  return (
    <AIReportSuggestions
      reports={existingReports}
      context="quarterly_review"
      onSuggestionApply={handleSuggestion}
    />
  );
};
```

### Smart Placeholders for Templates

```typescript
const TemplateEditor = () => {
  const [template, setTemplate] = useState("");

  const insertPlaceholder = (placeholder: AIPlaceholder) => {
    const placeholderText = `{{${placeholder.name}}}`;
    setTemplate((prev) => prev + placeholderText);
  };

  return (
    <div>
      <textarea
        value={template}
        onChange={(e) => setTemplate(e.target.value)}
      />
      <AISmartPlaceholders
        context="executive_summary"
        industry="finance"
        onPlaceholderSelect={insertPlaceholder}
      />
    </div>
  );
};
```

## Performance Considerations

1. **Lazy Loading**: Components are lazy-loaded to reduce initial bundle size
2. **Memoization**: Expensive calculations are memoized
3. **Debouncing**: User input is debounced to prevent excessive API calls
4. **Caching**: Results are cached where appropriate

## Accessibility

- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: Meets WCAG 2.1 AA standards
- **Focus Management**: Clear focus indicators and logical tab order

## Testing

Components include comprehensive test coverage:

- Unit tests for individual component logic
- Integration tests for AI service interaction
- E2E tests for complete user workflows
- Mock data for consistent testing

## Development

### Adding New AI Features

1. Add interface to `aiService.ts`
2. Implement backend endpoint
3. Create React component
4. Add to AIHub tabs
5. Update documentation

### Customization

Components accept custom styling through MUI's `sx` prop and theme customization:

```typescript
<AIAnalysisDashboard
  data={data}
  sx={{ backgroundColor: "custom.background" }}
/>
```

## Troubleshooting

### Common Issues

1. **AI Service Unavailable**

   - Check backend connectivity
   - Verify API endpoints
   - Review fallback mechanisms

2. **Slow Performance**

   - Enable data caching
   - Optimize data payload size
   - Consider pagination for large datasets

3. **TypeScript Errors**
   - Ensure proper interface imports
   - Check data structure matching
   - Verify callback function signatures

### Debug Mode

Enable debug logging:

```typescript
// In development
if (process.env.NODE_ENV === "development") {
  console.log("AI Component Debug:", { data, result });
}
```

## Future Enhancements

- Real-time AI suggestions
- Custom AI model training
- Advanced data visualization
- Multi-language support
- Voice interaction capabilities
