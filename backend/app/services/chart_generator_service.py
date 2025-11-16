"""
Chart Generator Service
Generates chart images (PNG) from data for embedding in reports
"""

import os
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import io
import base64

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("matplotlib not available - chart generation will be limited")
    MATPLOTLIB_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.warning("PIL/Pillow not available - image processing will be limited")
    PIL_AVAILABLE = False


class ChartGeneratorService:
    """Service for generating chart images from data"""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'static', 'charts')
        self.ensure_output_directory()

    def ensure_output_directory(self):
        """Ensure the output directory exists"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def generate_bar_chart(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate a bar chart from data

        Args:
            data: List of data records
            config: Chart configuration (title, xField, yField, colors, etc.)

        Returns:
            Tuple of (file_path, base64_encoded_image)
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for chart generation")

        try:
            # Extract configuration
            title = config.get('title', 'Bar Chart')
            group_by = config.get('groupBy')
            x_field = config.get('xField', 'name')
            y_field = config.get('yField', 'value')
            color = config.get('color', config.get('colors', ['#3b82f6'])[0] if isinstance(config.get('colors'), list) else '#3b82f6')
            orientation = config.get('orientation', 'vertical')  # 'vertical' or 'horizontal'
            show_percentage = config.get('showPercentage', False)
            categories = config.get('categories', [])  # Predefined category order

            # Extract and process data
            x_values = []
            y_values = []

            # If groupBy is specified, aggregate data by counting occurrences
            if group_by:
                from collections import Counter
                group_counts = Counter()
                for record in data:
                    if group_by in record and record[group_by]:
                        value = str(record[group_by]).strip()
                        if value:
                            group_counts[value] += 1

                # Use predefined categories if provided, otherwise use counts
                if categories:
                    # Ensure all categories are present, even if count is 0
                    for category in categories:
                        x_values.append(category)
                        y_values.append(group_counts.get(category, 0))
                else:
                    # Use most common
                    for label, count in group_counts.most_common():
                        x_values.append(label)
                        y_values.append(count)

                logger.info(f"📊 Bar chart grouped by '{group_by}': {dict(group_counts)}")
            else:
                # Original behavior: use xField and yField
                for record in data:
                    if x_field in record and y_field in record:
                        x_values.append(str(record[x_field]))
                        try:
                            y_values.append(float(record[y_field]))
                        except (ValueError, TypeError):
                            y_values.append(0)

            if not x_values or not y_values:
                logger.warning("No valid data for bar chart")
                return None, None

            # Calculate percentages if needed
            total = sum(y_values)
            percentages = [(v/total*100) if total > 0 else 0 for v in y_values]

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))

            if orientation == 'horizontal':
                bars = ax.barh(x_values, y_values, color=color, alpha=0.9)

                # Add labels on bars (values and/or percentages)
                for idx, (bar, value, pct) in enumerate(zip(bars, y_values, percentages)):
                    width = bar.get_width()
                    if show_percentage:
                        label = f'{pct:.0f}%' if value > 0 else f'{pct:.1f}%'
                    else:
                        label = f'{value:.0f}'

                    ax.text(width, bar.get_y() + bar.get_height()/2.,
                           f'  {label}',
                           ha='left', va='center', fontsize=10, fontweight='bold')

                ax.set_xlabel('PERATUS' if show_percentage else 'COUNT', fontsize=11)
                ax.set_xlim(0, max(percentages) * 1.2 if show_percentage else max(y_values) * 1.2)
            else:
                bars = ax.bar(x_values, y_values, color=color, alpha=0.8)

                # Add value labels on bars
                for bar, value, pct in zip(bars, y_values, percentages):
                    height = bar.get_height()
                    if show_percentage:
                        label = f'{pct:.1f}%'
                    else:
                        label = f'{value:.1f}'
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=9)

                ax.set_ylabel('PERATUS' if show_percentage else 'COUNT', fontsize=11)

                # Rotate x labels if too many
                if len(x_values) > 5:
                    plt.xticks(rotation=45, ha='right')

            # Styling
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.grid(axis='x' if orientation == 'horizontal' else 'y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            # Save to file and get base64
            file_path, base64_data = self._save_and_encode_chart(fig, 'bar_chart')
            plt.close(fig)

            logger.info(f"✅ Bar chart generated: {file_path}")
            return file_path, base64_data

        except Exception as e:
            logger.error(f"❌ Error generating bar chart: {str(e)}")
            raise

    def generate_line_chart(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[str, str]:
        """Generate a line chart from data"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for chart generation")

        try:
            # Extract configuration
            title = config.get('title', 'Line Chart')
            x_field = config.get('xField', 'name')
            y_field = config.get('yField', 'value')
            color = config.get('colors', ['#10b981'])[0]

            # Extract data
            x_values = []
            y_values = []
            for record in data:
                if x_field in record and y_field in record:
                    x_values.append(str(record[x_field]))
                    try:
                        y_values.append(float(record[y_field]))
                    except (ValueError, TypeError):
                        y_values.append(0)

            if not x_values or not y_values:
                logger.warning("No valid data for line chart")
                return None, None

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(x_values, y_values, color=color, linewidth=2.5, marker='o',
                   markersize=8, alpha=0.8)

            # Add value labels
            for i, (x, y) in enumerate(zip(x_values, y_values)):
                ax.text(i, y, f'{y:.1f}', ha='center', va='bottom', fontsize=9)

            # Styling
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(x_field.replace('_', ' ').title(), fontsize=11)
            ax.set_ylabel(y_field.replace('_', ' ').title(), fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--')

            if len(x_values) > 5:
                plt.xticks(rotation=45, ha='right')

            plt.tight_layout()

            # Save to file and get base64
            file_path, base64_data = self._save_and_encode_chart(fig, 'line_chart')
            plt.close(fig)

            logger.info(f"✅ Line chart generated: {file_path}")
            return file_path, base64_data

        except Exception as e:
            logger.error(f"❌ Error generating line chart: {str(e)}")
            raise

    def generate_pie_chart(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[str, str]:
        """Generate a pie chart from data"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for chart generation")

        try:
            # Extract configuration
            title = config.get('title', 'Pie Chart')
            group_by = config.get('groupBy')  # Field to group by (e.g., 'penilaian', 'jantina')
            name_field = config.get('nameField', 'name')
            value_field = config.get('valueField', 'value')
            colors = config.get('colors', ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'])

            # Extract and process data
            labels = []
            values = []

            # If groupBy is specified, aggregate data by counting occurrences
            if group_by:
                from collections import Counter
                # Count occurrences of each value in the groupBy field
                group_counts = Counter()
                for record in data:
                    if group_by in record and record[group_by]:
                        value = str(record[group_by]).strip()
                        if value:  # Only count non-empty values
                            group_counts[value] += 1

                # Convert to lists
                for label, count in group_counts.most_common():
                    labels.append(label)
                    values.append(count)

                logger.info(f"📊 Pie chart grouped by '{group_by}': {dict(group_counts)}")
            else:
                # Original behavior: use nameField and valueField
                for record in data:
                    if name_field in record and value_field in record:
                        labels.append(str(record[name_field]))
                        try:
                            values.append(float(record[value_field]))
                        except (ValueError, TypeError):
                            values.append(0)

            if not labels or not values:
                logger.warning("No valid data for pie chart")
                return None, None

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 8))
            wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors[:len(labels)],
                                              autopct='%1.1f%%', startangle=90,
                                              textprops={'fontsize': 10})

            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            # Styling
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()

            # Save to file and get base64
            file_path, base64_data = self._save_and_encode_chart(fig, 'pie_chart')
            plt.close(fig)

            logger.info(f"✅ Pie chart generated: {file_path}")
            return file_path, base64_data

        except Exception as e:
            logger.error(f"❌ Error generating pie chart: {str(e)}")
            raise

    def _save_and_encode_chart(self, fig, chart_type: str) -> Tuple[str, str]:
        """Save chart to file and return base64 encoded version"""
        from datetime import datetime

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{chart_type}_{timestamp}.png"
        file_path = os.path.join(self.output_dir, filename)

        # Save to file
        fig.savefig(file_path, dpi=150, bbox_inches='tight', facecolor='white')

        # Also encode as base64 for inline embedding
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        base64_data = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        return file_path, base64_data

    def generate_chart_from_config(self, chart_config: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate any chart type based on configuration

        Args:
            chart_config: Chart configuration with type, data, and options

        Returns:
            Tuple of (file_path, base64_encoded_image)
        """
        chart_type = chart_config.get('chartType', 'bar')
        data = chart_config.get('data', [])
        config = chart_config.get('config', chart_config)  # Support both formats

        if chart_type == 'bar':
            return self.generate_bar_chart(data, config)
        elif chart_type == 'line':
            return self.generate_line_chart(data, config)
        elif chart_type == 'pie':
            return self.generate_pie_chart(data, config)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")


# Global instance
chart_generator_service = ChartGeneratorService()
