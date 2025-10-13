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
