"""Reduced-order sprinkler research demonstrator; no experimental validation implied."""

from .config import Case
from .solver import simulate

__version__ = "0.2.1"
__all__ = ["Case", "simulate"]
