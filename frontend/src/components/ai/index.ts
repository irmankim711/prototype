// AI Components
export { default as AIHub } from "./AIHub";
export { default as AIAnalysisDashboard } from "./AIAnalysisDashboard";
export { default as AIReportSuggestions } from "./AIReportSuggestions";
export { default as AISmartPlaceholders } from "./AISmartPlaceholders";

// Re-export types from service for convenience
export type {
  AIAnalysisResult,
  AIReportSuggestion,
  AIReportSuggestionsResult,
  AIPlaceholder,
  AIPlaceholdersResult,
  AIValidationResult,
} from "../../services/aiService";
