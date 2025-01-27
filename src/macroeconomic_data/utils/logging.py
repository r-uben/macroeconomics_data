"""
Logging Configuration

This module provides logging setup utilities for the macroeconomic data package.
"""

import logging
import sys
from typing import Optional

def setup_logging(level: Optional[int] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Optional logging level (defaults to INFO if not specified)
    """
    if level is None:
        level = logging.INFO
        
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our configured handler
    root_logger.addHandler(stream_handler) 