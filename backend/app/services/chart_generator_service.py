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
            x_field = config.get('xField', 'name')
            y_field = config.get('yField', 'value')
            color = config.get('colors', ['#3b82f6'])[0]

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
                logger.warning("No valid data for bar chart")
                return None, None

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(x_values, y_values, color=color, alpha=0.8)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)

            # Styling
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(x_field.replace('_', ' ').title(), fontsize=11)
            ax.set_ylabel(y_field.replace('_', ' ').title(), fontsize=11)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Rotate x labels if too many
            if len(x_values) > 5:
                plt.xticks(rotation=45, ha='right')

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
            name_field = config.get('nameField', 'name')
            value_field = config.get('valueField', 'value')
            colors = config.get('colors', ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'])

            # Extract data
            labels = []
            values = []
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
