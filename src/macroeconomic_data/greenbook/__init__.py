"""
Greenbook/Tealbook data package.
This module contains functionality for fetching and processing Greenbook/Tealbook data from Philadelphia Fed.
"""

from .services.data_fetcher import GreenBookDataFetcher

__all__ = ['GreenBookDataFetcher'] 