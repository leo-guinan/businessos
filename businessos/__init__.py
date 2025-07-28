"""
Business OS: Business-as-Code Platform

A Domain-Specific Intelligence (DSI) platform that treats business operations
as executable, versioned specifications.
"""

__version__ = "0.1.0"
__author__ = "Business OS Team"
__email__ = "team@businessos.dev"

from .core.ontology import Ontology
from .core.compiler import Compiler
from .core.validator import Validator

__all__ = ["Ontology", "Compiler", "Validator"] 