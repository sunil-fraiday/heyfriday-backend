from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
from .base import ChartGenerator


class LineChartGenerator(ChartGenerator):
    """Generator for line charts"""

    def generate(self, data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> bytes:
        options = options or {}

        # Extract data
        x_data = data.get("x", [])
        y_data = data.get("y", [])

        if not x_data or not y_data:
            raise ValueError("Line chart requires 'x' and 'y' data")

        # Create figure and axes
        fig, ax = plt.subplots(figsize=options.get("figsize", (10, 6)))

        # Plot data
        ax.plot(
            x_data,
            y_data,
            marker=options.get("marker", "o"),
            linestyle=options.get("linestyle", "-"),
            color=options.get("color", "blue"),
        )

        # Set labels and title
        ax.set_xlabel(options.get("xlabel", ""))
        ax.set_ylabel(options.get("ylabel", ""))
        ax.set_title(options.get("title", "Line Chart"))

        # Add grid if specified
        if options.get("grid", False):
            ax.grid(True)

        # Save to bytes and return
        return self._save_to_bytes(fig)


class BarChartGenerator(ChartGenerator):
    """Generator for bar charts"""

    def generate(self, data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> bytes:
        options = options or {}

        # Extract data
        x_data = data.get("x", [])
        y_data = data.get("y", [])

        if not x_data or not y_data:
            raise ValueError("Bar chart requires 'x' and 'y' data")

        # Create figure and axes
        fig, ax = plt.subplots(figsize=options.get("figsize", (10, 6)))

        # Plot data
        ax.bar(x_data, y_data, color=options.get("color", "blue"), width=options.get("width", 0.7))

        # Set labels and title
        ax.set_xlabel(options.get("xlabel", ""))
        ax.set_ylabel(options.get("ylabel", ""))
        ax.set_title(options.get("title", "Bar Chart"))

        # Add grid if specified
        if options.get("grid", False):
            ax.grid(True, axis="y")

        # Save to bytes and return
        return self._save_to_bytes(fig)


class PieChartGenerator(ChartGenerator):
    """Generator for pie charts"""

    def generate(self, data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> bytes:
        options = options or {}

        # Extract data
        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values:
            raise ValueError("Pie chart requires 'labels' and 'values' data")

        # Create figure and axes
        fig, ax = plt.subplots(figsize=options.get("figsize", (10, 6)))

        # Plot data
        ax.pie(
            values,
            labels=labels,
            autopct=options.get("autopct", "%1.1f%%"),
            shadow=options.get("shadow", False),
            startangle=options.get("startangle", 90),
        )

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis("equal")

        # Set title
        ax.set_title(options.get("title", "Pie Chart"))

        # Save to bytes and return
        return self._save_to_bytes(fig)


def get_chart_generator(chart_type: str) -> ChartGenerator:
    """Factory function to get the appropriate chart generator"""
    generators = {
        "line": LineChartGenerator(),
        "bar": BarChartGenerator(),
        "pie": PieChartGenerator(),
    }

    if chart_type not in generators:
        supported_types = ", ".join(generators.keys())
        raise ValueError(f"Unsupported chart type: {chart_type}. Supported types: {supported_types}")

    return generators[chart_type]
