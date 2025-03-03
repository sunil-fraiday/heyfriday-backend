import io
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional


class ChartGenerator:
    """Base class for chart generation"""

    def generate(self, data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate a chart based on the provided data and options

        Args:
            data: The data to visualize
            options: Optional configuration for the chart

        Returns:
            The chart as bytes
        """
        raise NotImplementedError

    def _save_to_bytes(self, fig) -> bytes:
        """Save a matplotlib figure to bytes"""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
