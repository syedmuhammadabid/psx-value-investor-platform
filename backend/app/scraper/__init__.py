"""PSX data ingestion pipeline (parsers, normalization, validation).

The pipeline is source-agnostic: records arrive as ``RawFinancialRecord``
instances (today from a local file adapter; a real HTTP/PDF scraper can be
dropped in later without changing normalization, validation, or ingestion).
"""

from app.scraper import normalize, prices, validation

__all__ = ["normalize", "prices", "validation"]
