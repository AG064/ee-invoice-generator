"""
ee-invoice-generator - Estonian e-invoice generator
Generates XML invoices conforming to Estonian e-invoice standard (EN 16931)
"""
from .generator import InvoiceGenerator

__all__ = ["InvoiceGenerator"]