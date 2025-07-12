"""
Gemini Batch Tools

Command-line tools for managing Google Gemini batch jobs.
"""

from importlib.metadata import version

__version__ = version("gemini-batch")
__license__ = "CC0-1.0"

from . import submit, poll

__all__ = ["submit", "poll"]
