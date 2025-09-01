"""
Mechanical Drawing Analyzer Package

AI-powered analysis of mechanical engineering drawings.
"""

from .analyzer import MechanicalDrawingAnalyzer, PartSpecification
from .batch_processor import BatchProcessor, IncrementalProcessor
from .compliance_rules import ComplianceChecker

__version__ = "0.1.0"
__author__ = "Your Name (with AI assistance from Claude)"
__all__ = [
    "MechanicalDrawingAnalyzer",
    "PartSpecification", 
    "BatchProcessor",
    "IncrementalProcessor",
    "ComplianceChecker"
]