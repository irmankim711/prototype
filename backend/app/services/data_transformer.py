"""
Data Transformation and Aggregation Service
Provides data processing, filtering, grouping, and aggregation for reports
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataTransformer:
    """Service for transforming and aggregating data for reports"""

    def __init__(self):
        self.supported_aggregations = {
            'count': self._agg_count,
            'sum': self._agg_sum,
            'avg': self._agg_avg,
            'mean': self._agg_avg,  # Alias for avg
            'min': self._agg_min,
            'max': self._agg_max,
            'std': self._agg_std,
            'median': self._agg_median,
            'first': self._agg_first,
            'last': self._agg_last,
            'unique': self._agg_unique,
            'concat': self._agg_concat
        }

    def transform_data(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform data according to configuration

        Args:
            data: List of data records
            config: Transformation configuration

        Returns:
            Dictionary with transformed data and metadata
        """
        try:
            if not data:
                return {
                    'success': True,
                    'data': [],
                    'metadata': {'original_count': 0, 'transformed_count': 0}
                }

            # Convert to DataFrame for easier processing
            df = pd.DataFrame(data)
            original_count = len(df)

            logger.info(f"Starting data transformation with {original_count} records")

            # Apply filters
            if config.get('filters'):
                df = self._apply_filters(df, config['filters'])
                logger.info(f"After filtering: {len(df)} records")

            # Apply column transformations
            if config.get('column_transforms'):
                df = self._apply_column_transforms(df, config['column_transforms'])

            # Apply grouping and aggregation
            if config.get('group_by') or config.get('aggregations'):
                df = self._apply_grouping(df, config)
                logger.info(f"After grouping: {len(df)} records")

            # Apply sorting
            if config.get('sort_by'):
                df = self._apply_sorting(df, config['sort_by'])

            # Apply row limits
            if config.get('limit'):
                df = df.head(config['limit'])

            # Convert back to list of dictionaries
            transformed_data = df.to_dict('records')

            # Clean NaN values
            for record in transformed_data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None

            return {
                'success': True,
                'data': transformed_data,
                'metadata': {
                    'original_count': original_count,
                    'transformed_count': len(transformed_data),
                    'columns': list(df.columns),
                    'transformations_applied': {
                        'filters': bool(config.get('filters')),
                        'column_transforms': bool(config.get('column_transforms')),
                        'grouping': bool(config.get('group_by') or config.get('aggregations')),
                        'sorting': bool(config.get('sort_by')),
                        'limit': config.get('limit')
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': data,  # Return original data on error
                'metadata': {'original_count': len(data)}
            }

    def _apply_filters(self, df: pd.DataFrame, filters: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply filters to DataFrame"""
        for filter_config in filters:
            column = filter_config.get('column')
            operator = filter_config.get('operator', 'eq')
            value = filter_config.get('value')

            if not column or column not in df.columns:
                continue

            try:
                if operator == 'eq':
                    df = df[df[column] == value]
                elif operator == 'ne':
                    df = df[df[column] != value]
                elif operator == 'gt':
                    df = df[df[column] > value]
                elif operator == 'gte':
                    df = df[df[column] >= value]
                elif operator == 'lt':
                    df = df[df[column] < value]
                elif operator == 'lte':
                    df = df[df[column] <= value]
                elif operator == 'in':
                    if isinstance(value, list):
                        df = df[df[column].isin(value)]
                elif operator == 'not_in':
                    if isinstance(value, list):
                        df = df[~df[column].isin(value)]
                elif operator == 'contains':
                    df = df[df[column].astype(str).str.contains(str(value), na=False)]
                elif operator == 'starts_with':
                    df = df[df[column].astype(str).str.startswith(str(value), na=False)]
                elif operator == 'ends_with':
                    df = df[df[column].astype(str).str.endswith(str(value), na=False)]
                elif operator == 'regex':
                    df = df[df[column].astype(str).str.match(str(value), na=False)]
                elif operator == 'is_null':
                    df = df[df[column].isnull()]
                elif operator == 'is_not_null':
                    df = df[df[column].notnull()]

            except Exception as e:
                logger.warning(f"Error applying filter {filter_config}: {str(e)}")
                continue

        return df

    def _apply_column_transforms(self, df: pd.DataFrame, transforms: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply column transformations"""
        for transform in transforms:
            column = transform.get('column')
            operation = transform.get('operation')
            new_column = transform.get('new_column', column)

            if not column or column not in df.columns:
                continue

            try:
                if operation == 'uppercase':
                    df[new_column] = df[column].astype(str).str.upper()
                elif operation == 'lowercase':
                    df[new_column] = df[column].astype(str).str.lower()
                elif operation == 'capitalize':
                    df[new_column] = df[column].astype(str).str.capitalize()
                elif operation == 'trim':
                    df[new_column] = df[column].astype(str).str.strip()
                elif operation == 'extract_date':
                    df[new_column] = pd.to_datetime(df[column], errors='coerce').dt.date
                elif operation == 'extract_year':
                    df[new_column] = pd.to_datetime(df[column], errors='coerce').dt.year
                elif operation == 'extract_month':
                    df[new_column] = pd.to_datetime(df[column], errors='coerce').dt.month
                elif operation == 'extract_day':
                    df[new_column] = pd.to_datetime(df[column], errors='coerce').dt.day
                elif operation == 'to_numeric':
                    df[new_column] = pd.to_numeric(df[column], errors='coerce')
                elif operation == 'multiply':
                    factor = transform.get('factor', 1)
                    df[new_column] = pd.to_numeric(df[column], errors='coerce') * factor
                elif operation == 'divide':
                    divisor = transform.get('divisor', 1)
                    df[new_column] = pd.to_numeric(df[column], errors='coerce') / divisor
                elif operation == 'substring':
                    start = transform.get('start', 0)
                    end = transform.get('end')
                    if end:
                        df[new_column] = df[column].astype(str).str[start:end]
                    else:
                        df[new_column] = df[column].astype(str).str[start:]
                elif operation == 'replace':
                    old_value = transform.get('old_value', '')
                    new_value = transform.get('new_value', '')
                    df[new_column] = df[column].astype(str).str.replace(old_value, new_value)
                elif operation == 'concat':
                    other_columns = transform.get('other_columns', [])
                    separator = transform.get('separator', ' ')
                    concat_cols = [column] + other_columns
                    df[new_column] = df[concat_cols].astype(str).agg(separator.join, axis=1)

            except Exception as e:
                logger.warning(f"Error applying transform {transform}: {str(e)}")
                continue

        return df

    def _apply_grouping(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Apply grouping and aggregation"""
        group_by = config.get('group_by', [])
        aggregations = config.get('aggregations', {})

        if not group_by and not aggregations:
            return df

        try:
            if group_by:
                # Ensure all group_by columns exist
                valid_group_by = [col for col in group_by if col in df.columns]
                if not valid_group_by:
                    return df

                grouped = df.groupby(valid_group_by)

                # Apply aggregations
                agg_results = {}
                for column, agg_functions in aggregations.items():
                    if column not in df.columns:
                        continue

                    if isinstance(agg_functions, str):
                        agg_functions = [agg_functions]

                    for agg_func in agg_functions:
                        if agg_func in self.supported_aggregations:
                            result_column = f"{column}_{agg_func}"
                            agg_results[result_column] = grouped[column].apply(
                                self.supported_aggregations[agg_func]
                            )

                # Create result DataFrame
                if agg_results:
                    result_df = pd.DataFrame(agg_results).reset_index()
                else:
                    # Just group and count
                    result_df = grouped.size().reset_index(name='count')

                return result_df

            else:
                # Apply aggregations without grouping (overall statistics)
                agg_results = {}
                for column, agg_functions in aggregations.items():
                    if column not in df.columns:
                        continue

                    if isinstance(agg_functions, str):
                        agg_functions = [agg_functions]

                    for agg_func in agg_functions:
                        if agg_func in self.supported_aggregations:
                            result_column = f"{column}_{agg_func}"
                            agg_results[result_column] = self.supported_aggregations[agg_func](df[column])

                # Return single row DataFrame with aggregated values
                return pd.DataFrame([agg_results])

        except Exception as e:
            logger.error(f"Error applying grouping: {str(e)}")
            return df

    def _apply_sorting(self, df: pd.DataFrame, sort_config: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply sorting to DataFrame"""
        try:
            sort_columns = []
            ascending = []

            for sort_item in sort_config:
                column = sort_item.get('column')
                direction = sort_item.get('direction', 'asc').lower()

                if column and column in df.columns:
                    sort_columns.append(column)
                    ascending.append(direction == 'asc')

            if sort_columns:
                df = df.sort_values(by=sort_columns, ascending=ascending)

            return df

        except Exception as e:
            logger.error(f"Error applying sorting: {str(e)}")
            return df

    # Aggregation functions
    def _agg_count(self, series: pd.Series) -> int:
        """Count non-null values"""
        return series.count()

    def _agg_sum(self, series: pd.Series) -> float:
        """Sum of values"""
        return series.sum()

    def _agg_avg(self, series: pd.Series) -> float:
        """Average of values"""
        return series.mean()

    def _agg_min(self, series: pd.Series) -> Any:
        """Minimum value"""
        return series.min()

    def _agg_max(self, series: pd.Series) -> Any:
        """Maximum value"""
        return series.max()

    def _agg_std(self, series: pd.Series) -> float:
        """Standard deviation"""
        return series.std()

    def _agg_median(self, series: pd.Series) -> float:
        """Median value"""
        return series.median()

    def _agg_first(self, series: pd.Series) -> Any:
        """First value"""
        return series.iloc[0] if len(series) > 0 else None

    def _agg_last(self, series: pd.Series) -> Any:
        """Last value"""
        return series.iloc[-1] if len(series) > 0 else None

    def _agg_unique(self, series: pd.Series) -> int:
        """Count of unique values"""
        return series.nunique()

    def _agg_concat(self, series: pd.Series) -> str:
        """Concatenate string values"""
        return ', '.join(series.dropna().astype(str).unique())

    def generate_pivot_table(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate pivot table from data

        Args:
            data: List of data records
            config: Pivot configuration

        Returns:
            Dictionary with pivot table data
        """
        try:
            if not data:
                return {'success': True, 'data': [], 'metadata': {}}

            df = pd.DataFrame(data)

            rows = config.get('rows', [])
            columns = config.get('columns', [])
            values = config.get('values', [])
            aggfunc = config.get('aggfunc', 'count')

            # Validate columns exist
            all_columns = rows + columns + values
            missing_columns = [col for col in all_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success': False,
                    'error': f"Missing columns: {missing_columns}",
                    'data': []
                }

            # Create pivot table
            pivot_table = pd.pivot_table(
                df,
                index=rows if rows else None,
                columns=columns if columns else None,
                values=values if values else None,
                aggfunc=aggfunc,
                fill_value=0
            )

            # Convert to records format
            if isinstance(pivot_table.columns, pd.MultiIndex):
                # Handle MultiIndex columns
                pivot_data = pivot_table.reset_index().to_dict('records')
            else:
                pivot_data = pivot_table.reset_index().to_dict('records')

            return {
                'success': True,
                'data': pivot_data,
                'metadata': {
                    'rows': rows,
                    'columns': columns,
                    'values': values,
                    'aggfunc': aggfunc,
                    'shape': pivot_table.shape
                }
            }

        except Exception as e:
            logger.error(f"Error generating pivot table: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def calculate_statistics(self, data: List[Dict[str, Any]], columns: List[str] = None) -> Dict[str, Any]:
        """
        Calculate statistical summary for numeric columns

        Args:
            data: List of data records
            columns: Specific columns to analyze (if None, analyze all numeric columns)

        Returns:
            Dictionary with statistical summary
        """
        try:
            if not data:
                return {'success': True, 'statistics': {}}

            df = pd.DataFrame(data)

            # Select numeric columns
            if columns:
                numeric_columns = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
            else:
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

            statistics = {}
            for col in numeric_columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    statistics[col] = {
                        'count': len(col_data),
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'q25': float(col_data.quantile(0.25)),
                        'q75': float(col_data.quantile(0.75)),
                        'sum': float(col_data.sum()),
                        'null_count': int(df[col].isnull().sum())
                    }

            return {
                'success': True,
                'statistics': statistics,
                'metadata': {
                    'total_records': len(df),
                    'numeric_columns': numeric_columns
                }
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'statistics': {}
            }


# Create singleton instance
data_transformer = DataTransformer()