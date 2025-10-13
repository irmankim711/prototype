# Enhanced Form Builder Dashboard Setup Script (PowerShell)
# This script helps set up the enhanced dashboard components on Windows

Write-Host "🎨 Setting up Enhanced Form Builder Dashboard..." -ForegroundColor Green

# Check if we're in the correct directory
if (!(Test-Path "package.json")) {
    Write-Host "❌ Error: Please run this script from the frontend root directory" -ForegroundColor Red
    exit 1
}

# Install additional dependencies if needed
Write-Host "📦 Installing additional dependencies..." -ForegroundColor Yellow

# Check if lodash is installed
$lodashInstalled = npm list lodash 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing lodash..." -ForegroundColor Cyan
    npm install lodash
    npm install --save-dev @types/lodash
}

# Check if Chart.js is installed
$chartjsInstalled = npm list chart.js 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Chart.js and react-chartjs-2..." -ForegroundColor Cyan
    npm install chart.js react-chartjs-2
}

# Create directories if they don't exist
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "src\theme" | Out-Null
New-Item -ItemType Directory -Force -Path "src\styles" | Out-Null
New-Item -ItemType Directory -Force -Path "src\pages\FormBuilderAdmin" | Out-Null
New-Item -ItemType Directory -Force -Path "src\hooks" | Out-Null
New-Item -ItemType Directory -Force -Path "src\utils" | Out-Null

# Create a development environment file
Write-Host "⚙️ Creating development configuration..." -ForegroundColor Yellow
@"
# Enhanced Dashboard Configuration
REACT_APP_DASHBOARD_VERSION=enhanced
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_QR_CODES=true
REACT_APP_ENABLE_EXTERNAL_FORMS=true
REACT_APP_DEBUG_MODE=true
"@ | Out-File -FilePath ".env.development.enhanced" -Encoding UTF8

# Create TypeScript configuration for the enhanced features
Write-Host "📋 Setting up TypeScript configuration..." -ForegroundColor Yellow
@"
// Enhanced Dashboard Type Definitions

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}

interface Window {
  // Enhanced dashboard globals
  __DASHBOARD_DEBUG__?: boolean;
  __PERFORMANCE_OBSERVER__?: PerformanceObserver;
  gtag?: (...args: any[]) => void;
}

// Chart.js module augmentation
declare module 'chart.js' {
  interface TooltipModel {
    // Add any custom tooltip properties
  }
}

// Lodash module augmentation
declare module 'lodash' {
  interface LoDashStatic {
    // Add any custom lodash methods if needed
  }
}
"@ | Out-File -FilePath "src\types\enhanced.d.ts" -Encoding UTF8

# Create a component index file for better imports
Write-Host "📋 Creating component index..." -ForegroundColor Yellow
@"
// Enhanced Form Builder Admin Exports
export { default as FormBuilderDashboardEnhanced } from './FormBuilderDashboardEnhanced';
export { default as FormBuilderAdmin } from './FormBuilderAdmin';
export { default as FormBuilderAdminFixed } from './FormBuilderAdminFixed';
export { default as FormBuilderAdminEnhanced } from './FormBuilderAdminEnhanced';

// Re-export types
export type { Form } from '../../services/formBuilder';
"@ | Out-File -FilePath "src\pages\FormBuilderAdmin\index.ts" -Encoding UTF8

# Create a custom hook for dashboard functionality
Write-Host "🪝 Creating custom hooks..." -ForegroundColor Yellow
@"
import { useState, useCallback, useMemo } from 'react';
import { debounce } from 'lodash';

export interface UseDashboardEnhancedProps {
  initialSearchQuery?: string;
  initialSortBy?: string;
  initialFilterStatus?: string;
}

export const useDashboardEnhanced = ({
  initialSearchQuery = '',
  initialSortBy = 'created_at',
  initialFilterStatus = 'all',
}: UseDashboardEnhancedProps = {}) => {
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [sortBy, setSortBy] = useState(initialSortBy);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterStatus, setFilterStatus] = useState(initialFilterStatus);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Debounced search
  const debouncedSearch = useCallback(
    (query: string) => {
      const handler = debounce((q: string) => {
        setSearchQuery(q);
      }, 300);
      handler(query);
    },
    []
  );

  // Filter and sort logic
  const processItems = useCallback(
    (items: any[]) => {
      const filtered = items.filter((item) => {
        const matchesSearch = item.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.description?.toLowerCase().includes(searchQuery.toLowerCase());
        
        const matchesStatus = filterStatus === 'all' || 
          (filterStatus === 'active' && item.is_active) ||
          (filterStatus === 'inactive' && !item.is_active);

        return matchesSearch && matchesStatus;
      });

      // Sort items
      filtered.sort((a, b) => {
        let aValue, bValue;
        
        switch (sortBy) {
          case 'title':
            aValue = a.title?.toLowerCase() || '';
            bValue = b.title?.toLowerCase() || '';
            break;
          case 'submissions':
            aValue = a.submission_count || 0;
            bValue = b.submission_count || 0;
            break;
          case 'updated_at':
            aValue = new Date(a.updated_at || 0).getTime();
            bValue = new Date(b.updated_at || 0).getTime();
            break;
          default:
            aValue = new Date(a.created_at || 0).getTime();
            bValue = new Date(b.created_at || 0).getTime();
        }

        if (sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });

      return filtered;
    },
    [searchQuery, sortBy, sortOrder, filterStatus]
  );

  return {
    searchQuery,
    sortBy,
    sortOrder,
    filterStatus,
    viewMode,
    debouncedSearch,
    setSortBy,
    setSortOrder,
    setFilterStatus,
    setViewMode,
    processItems,
  };
};
"@ | Out-File -FilePath "src\hooks\useDashboardEnhanced.ts" -Encoding UTF8

# Create accessibility utilities
Write-Host "♿ Creating accessibility utilities..." -ForegroundColor Yellow
@"
// Accessibility utility functions for the enhanced dashboard

export const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.setAttribute('class', 'sr-only');
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

export const trapFocus = (element: HTMLElement) => {
  const focusableElements = element.querySelectorAll(
    'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  };

  element.addEventListener('keydown', handleTabKey);
  firstElement?.focus();

  return () => {
    element.removeEventListener('keydown', handleTabKey);
  };
};

export const getColorContrast = (foreground: string, background: string): number => {
  // Simplified contrast calculation
  // In production, use a proper color contrast library
  const getLuminance = (color: string) => {
    // This is a simplified implementation
    // Use a proper color library for production
    return 0.5; // Placeholder
  };
  
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};
"@ | Out-File -FilePath "src\utils\accessibility.ts" -Encoding UTF8

# Create performance monitoring utilities
Write-Host "📊 Creating performance utilities..." -ForegroundColor Yellow
@"
// Performance monitoring utilities for the enhanced dashboard

export const measurePerformance = (name: string, fn: () => void) => {
  const start = performance.now();
  fn();
  const end = performance.now();
  
  console.log(\`\${name} took \${end - start} milliseconds\`);
  
  // Report to analytics if available
  if (window.gtag) {
    window.gtag('event', 'timing_complete', {
      name: name,
      value: Math.round(end - start),
    });
  }
};

export const observeElementPerformance = (element: HTMLElement, callback: (entry: IntersectionObserverEntry) => void) => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(callback);
  }, {
    threshold: 0.1,
  });
  
  observer.observe(element);
  
  return () => {
    observer.unobserve(element);
  };
};

export const preloadImages = (urls: string[]): Promise<void[]> => {
  return Promise.all(
    urls.map((url) => {
      return new Promise<void>((resolve) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => resolve(); // Still resolve to avoid blocking
        img.src = url;
      });
    })
  );
};
"@ | Out-File -FilePath "src\utils\performance.ts" -Encoding UTF8

Write-Host "✅ Enhanced Form Builder Dashboard setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "1. Import the enhanced dashboard in your main App component" -ForegroundColor White
Write-Host "2. Apply the enhanced theme to your Material-UI ThemeProvider" -ForegroundColor White
Write-Host "3. Import the enhanced CSS styles in your main CSS file" -ForegroundColor White
Write-Host "4. Test the new dashboard functionality" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "- Read ENHANCED_DASHBOARD_README.md for detailed information" -ForegroundColor White
Write-Host "- Check the src/pages/FormBuilderAdmin/FormBuilderDashboardEnhanced.tsx file" -ForegroundColor White
Write-Host "- Review the enhanced theme in src/theme/enhancedTheme.ts" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Happy coding!" -ForegroundColor Green
