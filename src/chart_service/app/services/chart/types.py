from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np

from app.schemas.chart import AxisTicksOptions
from .base import ChartGenerator


def apply_tick_options(ax: Axes, axis_type: str, tick_options: AxisTicksOptions):
    """
    Apply tick formatting options to the specified axis

    Args:
        ax: Matplotlib axis
        axis_type: 'x' or 'y' to specify which axis to format
        tick_options: Dictionary containing tick formatting options
    """
    if not tick_options:
        return

    # Get the current tick positions and labels
    if axis_type == "x":
        locs = ax.get_xticks()
        labels = [item.get_text() for item in ax.get_xticklabels()]
    else:
        locs = ax.get_yticks()
        labels = [item.get_text() for item in ax.get_yticklabels()]

    # If custom tick values are provided, use them
    if tick_options.values:
        locs = tick_options.values

    # If custom labels are provided, use them
    if tick_options.labels:
        labels = tick_options.labels

    # Apply step (show every nth tick)
    if tick_options.step and tick_options.step > 1:
        locs = locs[:: tick_options.step]
        if len(labels) >= len(locs):
            labels = labels[:: tick_options.step]

    # Set the tick positions and labels
    if axis_type == "x":
        ax.set_xticks(locs)
        if labels and len(labels) == len(locs):
            ax.set_xticklabels(labels)

        # Apply rotation if specified
        if tick_options.rotation is not None:
            plt.setp(ax.get_xticklabels(), rotation=tick_options.rotation)

        # Apply font size if specified
        if tick_options.fontsize is not None:
            plt.setp(ax.get_xticklabels(), fontsize=tick_options.fontsize)
    else:
        ax.set_yticks(locs)
        if labels and len(labels) == len(locs):
            ax.set_yticklabels(labels)

        # Apply rotation if specified
        if tick_options.rotation is not None:
            plt.setp(ax.get_yticklabels(), rotation=tick_options.rotation)

        # Apply font size if specified
        if tick_options.fontsize is not None:
            plt.setp(ax.get_yticklabels(), fontsize=tick_options.fontsize)


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

        # Apply custom tick options if provided
        if options.get("xticks"):
            apply_tick_options(ax, "x", AxisTicksOptions.model_validate(options.get("xticks")))

        if options.get("yticks"):
            apply_tick_options(ax, "y", AxisTicksOptions.model_validate(options.get("yticks")))

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

        # Apply custom tick options if provided
        if options.get("xticks"):
            apply_tick_options(ax, "x", AxisTicksOptions.model_validate(options.get("xticks")))

        if options.get("yticks"):
            apply_tick_options(ax, "y", AxisTicksOptions.model_validate(options.get("yticks")))

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

        # Note: Pie charts don't use the same axis system as other charts,
        # so we don't apply tick options here

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
