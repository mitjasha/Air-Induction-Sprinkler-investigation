"""Reduced-order sprinkler research demonstrator; no experimental validation implied."""

from .config import Case
from .solver import simulate

__version__ = "0.1.0"
__all__ = ["Case", "simulate"]
