#!/bin/bash

# Enhanced Form Builder Dashboard Setup Script
# This script helps set up the enhanced dashboard components

echo "🎨 Setting up Enhanced Form Builder Dashboard..."

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend root directory"
    exit 1
fi

# Install additional dependencies if needed
echo "📦 Installing additional dependencies..."

# Check if lodash is installed
if ! npm list lodash > /dev/null 2>&1; then
    echo "Installing lodash..."
    npm install lodash
    npm install --save-dev @types/lodash
fi

# Check if Chart.js is installed
if ! npm list chart.js > /dev/null 2>&1; then
    echo "Installing Chart.js and react-chartjs-2..."
    npm install chart.js react-chartjs-2
fi

# Create directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p src/theme
mkdir -p src/styles
mkdir -p src/pages/FormBuilderAdmin

# Copy theme file if it doesn't exist
if [ ! -f "src/theme/enhancedTheme.ts" ]; then
    echo "Creating enhanced theme..."
    # The theme file should already be created by the previous steps
fi

# Update package.json scripts if needed
echo "📝 Updating package.json scripts..."

# Add a linting script for the new files
if ! grep -q "lint:enhanced" package.json; then
    echo "Adding enhanced dashboard linting script..."
    # You can add custom scripts here if needed
fi

# Create a development environment file
echo "⚙️ Creating development configuration..."
cat > .env.development.enhanced << EOL
# Enhanced Dashboard Configuration
REACT_APP_DASHBOARD_VERSION=enhanced
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_QR_CODES=true
REACT_APP_ENABLE_EXTERNAL_FORMS=true
REACT_APP_DEBUG_MODE=true
EOL

# Create TypeScript configuration for the enhanced features
echo "📋 Setting up TypeScript configuration..."
cat > src/types/enhanced.d.ts << EOL
// Enhanced Dashboard Type Definitions

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}

interface Window {
  // Enhanced dashboard globals
  __DASHBOARD_DEBUG__?: boolean;
  __PERFORMANCE_OBSERVER__?: PerformanceObserver;
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
EOL

# Create a component index file for better imports
echo "📋 Creating component index..."
cat > src/pages/FormBuilderAdmin/index.ts << EOL
// Enhanced Form Builder Admin Exports
export { default as FormBuilderDashboardEnhanced } from './FormBuilderDashboardEnhanced';
export { default as FormBuilderAdmin } from './FormBuilderAdmin';
export { default as FormBuilderAdminFixed } from './FormBuilderAdminFixed';
export { default as FormBuilderAdminEnhanced } from './FormBuilderAdminEnhanced';

// Re-export types
export type { Form } from '../../services/formBuilder';
EOL

# Create a custom hook for dashboard functionality
echo "🪝 Creating custom hooks..."
mkdir -p src/hooks
cat > src/hooks/useDashboardEnhanced.ts << EOL
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
      let filtered = items.filter((item) => {
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
EOL

# Create accessibility utilities
echo "♿ Creating accessibility utilities..."
mkdir -p src/utils
cat > src/utils/accessibility.ts << EOL
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
EOL

# Create performance monitoring utilities
echo "📊 Creating performance utilities..."
cat > src/utils/performance.ts << EOL
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
EOL

echo "✅ Enhanced Form Builder Dashboard setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Import the enhanced dashboard in your main App component"
echo "2. Apply the enhanced theme to your Material-UI ThemeProvider"
echo "3. Import the enhanced CSS styles in your main CSS file"
echo "4. Test the new dashboard functionality"
echo ""
echo "📚 Documentation:"
echo "- Read ENHANCED_DASHBOARD_README.md for detailed information"
echo "- Check the src/pages/FormBuilderAdmin/FormBuilderDashboardEnhanced.tsx file"
echo "- Review the enhanced theme in src/theme/enhancedTheme.ts"
echo ""
echo "🚀 Happy coding!"
